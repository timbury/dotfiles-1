#!/bin/bash

dotfiles=$HOME/.dotfiles
configdir=$HOME/.config
cachedir=$HOME/.local/share
cd $HOME

if [[ "$1" != "-n" ]]; then
	# Create a directory
	function makedir {
		[[ ! -d $1 ]] && mkdir -p $1
	}

	# Create a symlink
	function link {
		[[ ! -r $2 ]] && ln -s $1 $2
	}

	# Fix terminal definition so C-H works properly in neovim
	function fixterm {
		infocmp $TERM | sed 's/kbs=^[hH]/kbs=\\177/' > /tmp/$TERM.ti
		tic /tmp/$TERM.ti
		rm /tmp/$TERM.ti
	}
else
	function makedir {
		echo "mkdir $1"
	}

	function link {
		echo "ln -s $1 -> $2"
	}

	function fixterm {
		echo "infocmp $TERM | sed 's/kbs=^[hH]/kbs=\\177/' > /tmp/$TERM.ti"
		echo "tic /tmp/$TERM.ti"
		echo "rm /tmp/$TERM.ti"
	}
fi

for f in $(ls $dotfiles/home); do
	link $dotfiles/home/$f $HOME/.$(basename $f)
done

for f in $(ls $dotfiles/config); do
	link $dotfiles/config/$f $HOME/.config/$(basename $f)
done

link $dotfiles/vim $HOME/.vim

makedir $cachedir/tmux/resurrect
makedir $cachedir/vim/session
makedir $cachedir/vim/swap
makedir $cachedir/vim/backup
makedir $cachedir/vim/undo
makedir $cachedir/zsh

makedir $configdir
link $dotfiles/vim $configdir/nvim

# Fix the terminal definition so that C-H works properly in neovim. This
# function may also need to be run for the tmux terminal type.
fixterm
