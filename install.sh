#!/bin/sh
if [ -f ~/.zshrc ]; then
	if grep -q "alias rui" ~/.zshrc; then
		echo "rui/scripts/install.sh: removing zsh rui alias"
		sed -i '.bak' '/# >>>>> RUI >>>>>/d' 									~/.zshrc
		sed -i '.bak' '/# !! Contents within this block are managed by RUI/d' 	~/.zshrc
		sed -i '.bak' '/alias rui=.*$/d'										~/.zshrc
		sed -i '.bak' '/# <<<<< RUI <<<<</d' 									~/.zshrc
		unalias rui 2>/dev/null
	fi
fi

if [ -f ~/.bashrc ]; then
	if grep -q "alias rui" ~/.bashrc; then
		echo "rui/scripts/install.sh: removing bash rui alias"
		sed -i '.bak' '/# >>>>> RUI >>>>>/d' 									~/.bashrc
		sed -i '.bak' '/# !! Contents within this block are managed by RUI/d' 	~/.bashrc
		sed -i '.bak' '/alias rui=.*$/d'										~/.bashrc
		sed -i '.bak' '/# <<<<< RUI <<<<</d' 									~/.bashrc
		unalias rui 2>/dev/null
	fi
fi

if [ ! -d ~/python ]; then
	echo "rui/scripts/install.sh: creating python virtual environment..."
	python3 -m venv ~/python
fi

if [ ! -f ~/python/bin/pipx ]; then
	echo "rui/scripts/install.sh: installing pipx..."
	~/python/bin/pip install pipx
fi

echo "rui/scripts/install.sh: installing RUI..."
~/python/bin/pipx ensurepath
~/python/bin/pipx install . --force
