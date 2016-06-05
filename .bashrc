# If not running interactively, don't do anything
[ -z "${PS1}" ] && return

# Add our bin directory to PATH
[ -d "${HOME}/bin" ] && PATH="${HOME}/bin:${PATH}"

# Add rubygems directory to PATH
[ -x $(command -v ruby >/dev/null 2>&1) ] && PATH="${PATH}:$(ruby -rubygems -e "puts Gem.user_dir")/bin"

# append to the history file, don't overwrite it
shopt -s histappend

# for setting history length see HISTSIZE and HISTFILESIZE in bash(1)
HISTSIZE=10000
HISTFILESIZE=10000

# check the window size after each command and, if necessary,
# update the values of LINES and COLUMNS.
shopt -s checkwinsize

# Intelligent history autocompletion
bind '"\e[A": history-search-backward'
bind '"\e[B": history-search-forward'

# Aliases
. "${HOME}/.config/aliases"

# Remove redundant mapping to allow rtorrent to work with screen
stty stop undef
stty start undef

# Functions
encrypt() { openssl aes-256-cbc -a -salt -in "${1}" -out "${1}.aes"; };
decrypt() { openssl aes-256-cbc -d -a -in "${1}" -out "${1:0:(-4)}"; };

# Exports
export EDITOR="vim"
export HISTCONTROL=ignoreboth:erasedups

# Colors
. "${HOME}/.config/colors"

# Prompt
. /usr/share/git/completion/git-prompt.sh # Loads __git_ps1
[ -f "${HOME}/.config/prompt" ] && . "${HOME}/.config/prompt"
