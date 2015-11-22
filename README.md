# Dot Files
This repository contains common dot files used across different machines.

The intent is that the files get "deployed" to their destinations once the repository is checked out. Deploying essentially means creating symbolic links from their intended destinations to their location in the checked out repository.

## How to use

Simply run `./deploy.py` to symlink all the files to their expected destination.

For adding new files, or customizing them for certain machines, please read below.

## Creation of a dot file
The structure of this repository should be a sparse version of the home directory. The files will have a symlink mirrored at the home directory following the relative path in this directory.

For example

    $HOME/.dotFiles
    ├── .config
    |   └── my_folder
    |       └──my_file
    
will generate

    $HOME
    ├── .config
    |   └── my_folder
    |       └──my_file --> $HOME/.dotFiles/.config/my_folder/my_file
    
Note that if the folders do not exist in the home directory, they will be created.

## Custom dot file for a user/host
A common problem is that when using multiple machines / users we want to have slightly different configurations for each user / machine.

This problem is solved by having the suffix
`<[user]|[host]|[user@host]>`. This is a special tag at the end of the file name that is understood by the `deploy.py` script.

What this format specifies is that only files matching the current user, host or combination of both will be symlinked (the tag will not be part of the symlink).

If multiple matches are found during execution, the precedence is `user@host > user > host > [nothing]`.

### Example
A common use case for this pattern is for having a custom prompt for root.

For root we could have `$HOME/.dotFiles/.config/prompt<root>`
    
    # A red prompt when we are root
    PS1='\[\e[0;31m\]\u$ \[\e[m\]\[\e[0;32m\]'
    
For a normal user we could have `$HOME/.dotFiles/.config/prompt<archie>`

    # A blue prompt as a normal user
    PS1='\[\e[0;34m\]\u$ \[\e[m\]\[\e[0;32m\]'
    
And keep a generic `$HOME/.dotFiles/.bashrc`

    # A generic .bashrc that just imports the prompt
    # ...
    source $HOME/.config/prompt
    # ...

When running `deploy.py` as `archie`, the following symlinks will be created

    $HOME
    ├── .config
    |   └── prompt --> $HOME/.dotfiles/.config/prompt<archie>
    └── .bashrc    --> $HOME/.dotfiles/.bashrc

## Sensitive files

Some applications require some credentials stored in plaintext (eg. [aurvote](https://aur.archlinux.org/packages/aurvote)) or sometimes we just want to have some personal information included in generic files (eg. aliases with hostnames in `~/.bashrc`). 

As this information is not going to be inside the generic dot file (or repo!), these files are stored in `~/.sensitive` to group them together and have `deploy.py` symlink the required files.

Consider that if the file is just going to be sourced by another, it is not needed to symlink it (See `.deployignore`). It can be sourced from `~/.sensitive`. This will allow us to use stricter permissions on the directory (0600) and keep all the information in one place.

## Deploy script options
`deploy.py` offers multiple options that can be seen with `deploy.py -h`.

`source`:
The root to analyze recursively for files to be symlinked following the 'custom tag' matching.

`destination`:
The destination root. This is where the directory structure of `source` will be mirrored and symlinks created.

`--username`:
Override the username used when finding 'custom files' for deployment. By default it uses the current user.

`--hostname`:
Override the host used when finding 'custom files' for deployment. By default it uses the current machine's hostname.

`--ignorefile`:
If a `.deployignore` file is found, it will be used to find patterns to ignore when processing files/folders. A different file can be specified instead. The format of the file is a list where every line is a glob pattern.

`-v, --verbose`:
Print more output when executing

`-n, --dry`:
Simulate execution of this script. It will just show what files / directories would be created and in which location.

`--force`:
It may be the case that the destination files already exist. In this case, the script will fail for safety reasons. If you want to override the existing files, you can use this flag to first delete the destination.
