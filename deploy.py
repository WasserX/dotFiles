#!/usr/bin/python
"""This script provides a "deployment" utility for analyzing files from a
specified input directory and creating symlinks to them in the output directory.
The main purpose of this utility is to allow dot files to live in a source
controlled directory with symlinks to their expected destinations, allowing
better maintenance.

Certain rules are followed when creating the symlinks:
(1) The directory structure from 'input' is retained (ie. if input='/a',
output='/out' and a file 'a/b/my_file', the symlink will be in '/out/b/my_file')
(2) Missing directories will be created (ie. In the example above, '/out/b'
would be created if needed).
(3) Files ending with <[host]|[user]|[user@host]> will be treated as
specializations. In such cases, they MUST match the user and the hostname.
Only in such cases the files will be symlinked. If multiple such matches occur,
the precedence is user+host > user > host > [no specialization].
"""

import os
import argparse
import getpass
import socket
import re
import types
import fnmatch

class CPrinter:
    """Returns strings in the specified colors."""
    _cpurple = '\033[95m'
    _cblue = '\033[94m'
    _cgreen = '\033[92m'
    _cyellow = '\033[93m'
    _cred = '\033[91m'
    _no_color = '\033[0m'

    @staticmethod
    def __initialize__():
        colorattrs = (item for item in dir(CPrinter) if item.startswith('_c'))
        for attr in colorattrs:
            def color_text(self, msg, attr=attr):
                """Dynamically create a function to print in a color."""
                return CPrinter._clear(getattr(self, attr) + msg)
            setattr(CPrinter, attr[2:], types.MethodType(color_text, CPrinter))

    @staticmethod
    def _clear(text):
        """Get 'text' formatted to be printed without color."""
        return CPrinter._no_color + str(text) + CPrinter._no_color
CPrinter.__initialize__()


class SpecializedItem:
    """A file that can have a specialization at the end. It allows to extract
    a normalized filename without the specialization and its priority."""
    username = None
    host = None

    def __init__(self, directory, filename):
        self.filename = filename
        self.directory = directory
        self.destination = None
        self._specialization = None

        self._split_specialization()

    def _split_specialization(self):
        """Generate the specialization and destination name."""
        expression_matcher = '^(?P<name>.+?)(<(?P<specialization>[^<]*?)>$)?$'
        matcher = re.match(expression_matcher, self.filename)
        if matcher:
            matches = matcher.groupdict()
            self._specialization = matches['specialization']
            self.destination = matches['name']

    def is_valid(self):
        """Returns True if no specialization or if it matches user/hostname."""
        if self.destination and self._specialization is None:
            return True
        matcher = '^({host}|{user}(@{host})?)$'.format(
            user=SpecializedItem.username, host=SpecializedItem.host)
        return re.match(matcher, self._specialization) is not None

    def get_priority(self):
        """Returns the specialization priority. Higher is more precise."""
        if not self._specialization:
            return 0  # There is no specialization. Lowest valid priority

        matcher = '^({host}|({user}(@{host})?))$'.format(
            user=SpecializedItem.username, host=SpecializedItem.host)
        match = re.match(matcher, self._specialization)
        if not match:
            return -1  # Did not match, worse than no specialization
        return sum(1 for g in match.groups() if g)


class SymlinkContainer:
    """Maintain mapping of source --> destination symlink."""
    def __init__(self, source_root, destination_root):
        self._container = {}
        self.src_root = source_root
        self.dst_root = destination_root

    def add(self, item):
        """Add a new SpecializedItem. If another exists with lower priority it
        will be replaced."""
        dst_dir = os.path.join(self.dst_root,
                               os.path.relpath(item.directory, self.src_root))
        dst = os.path.abspath(os.path.join(dst_dir, item.destination))
        priority = item.get_priority()
        if (dst not in self._container or
                self._container[dst]['priority'] < priority):
            src = os.path.join(self.src_root, item.directory, item.filename)
            self._container[dst] = {'source': src, 'priority': priority}

    def generate(self, force, dry_mode):
        """Generate symlinks for the elements in this instance."""
        if dry_mode:
            print(CPrinter.yellow("Symlinks to create:"))  # pylint: disable=E1101
        else:
            print(CPrinter.yellow("Creating symlinks:"))  # pylint: disable=E1101
        for src, dst in self:
            if not dry_mode:
                if force and (os.path.isfile(dst) or os.path.islink(dst)):
                    print(CPrinter.red("Removing old {0}".format(dst)))  # pylint: disable=E1101
                    os.unlink(dst)
                os.symlink(src, dst)
            print("{1} --> {0}".format(CPrinter.blue(src), CPrinter.green(dst)))  # pylint: disable=E1101

    def __getitem__(self, destination):
        return (self._container[destination]['source'], destination)

    def __iter__(self):
        def generator():
            """Generator for iterating over the SymlinkContainer."""
            for key, value in self._container.items():
                yield (value['source'], key)
        return generator()


def ignore_matcher_creator(file_name):
    """Returns a function to check if a filename is in the ignore file."""

    matches = set()
    if os.path.isfile(file_name):
        with open(file_name, mode='r') as ignore_file:
            matches = set([l.strip() for l in ignore_file if l.strip()])

    return lambda item: next((m for m in matches if fnmatch.fnmatch(item, m)),
                             None)


def parse_arguments():
    """Parse command line arguments to the script."""
    parser = argparse.ArgumentParser(description='Create symlinks from source.')
    parser.add_argument('source', type=str, nargs='?', default=os.getcwd(),
                        help='root where symlinks sources will be.')
    parser.add_argument('destination', type=str, nargs='?',
                        default=os.path.expanduser("~"),
                        help='root where symlinks will be created.')
    parser.add_argument('--username', type=str, default=getpass.getuser(),
                        help='Override the username to match.')
    parser.add_argument('--hostname', type=str, default=socket.gethostname(),
                        help='Override the hostname to match.')
    parser.add_argument('--ignorefile', type=str, default='.deployignore',
                        help='File containing ignore rules.')
    parser.add_argument('-v', '--verbose', action='store_true')
    parser.add_argument('-n', '--dry', action='store_true',
                        help='just print output, do not make changes.')
    parser.add_argument('--force', action='store_true',
                        help='if destination exists, overwrite it.')

    return parser.parse_args()


def main():
    """Main method to be executed."""
    args = parse_arguments()
    if not args.dry:
        answer = input("No dry mode. Do you want to continue?[y/N]")
        if answer.lower() != "y":
            exit()

    source_root = os.path.abspath(args.source)
    destination_root = os.path.abspath(args.destination)
    ignored = ignore_matcher_creator(os.path.join(source_root, args.ignorefile))

    SpecializedItem.username = args.username
    SpecializedItem.host = args.hostname
    symlinks = SymlinkContainer(source_root, destination_root)
    directories = set()
    for root, dirs, files in os.walk(source_root):
        rel_subroot = os.path.relpath(root, source_root)
        if ignored(rel_subroot):
            print("Ignoring {0}".format(CPrinter.purple(root)))  # pylint: disable=E1101
            continue
        for name in files:
            item = SpecializedItem(root, name)
            if not item.is_valid() or ignored(item.filename):
                print("Ignoring {0}".format(CPrinter.purple(item.filename)))  # pylint: disable=E1101
                continue

            symlinks.add(item)

        if not dirs:
            dest_subroot = os.path.join(destination_root, rel_subroot)
            directories.add(os.path.abspath(dest_subroot))

    if args.verbose and args.dry:
        print(CPrinter.yellow("Directories to create:"))  # pylint: disable=E1101
    elif args.verbose:
        print(CPrinter.yellow("Creating directories:"))  # pylint: disable=E1101
    for directory in directories:
        try:
            if not args.dry:
                os.makedirs(directory)  # Creates intermediate directories
            if args.verbose:
                print(directory)
        except FileExistsError:
            if args.verbose:
                print("{0} already exists".format(directory))

    symlinks.generate(args.force, args.dry)


if __name__ == '__main__':
    main()
