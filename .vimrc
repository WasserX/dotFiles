set title

filetype plugin on
syntax on
color slate

set ts=4
set number
set ai

set spell
set spl=en


" Highlighting same words
autocmd CursorMoved * exe printf('match IncSearch /\V\<%s\>/', escape(expand('<cword>'), '/\'))
