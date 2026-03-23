#!/usr/bin/sh
if /usr/bin/grep -q "alias rui" ~/.zshrc; then
	echo "rui/scripts/install.sh: removing zsh rui alias"
	sed -i '/# >>>>> RUI >>>>>/d' 									~/.zshrc
	sed -i '/# !! Contents within this block are managed by RUI/d' 	~/.zshrc
	sed -i '/alias rui=.*$/d'										~/.zshrc
	sed -i '/# <<<<< RUI <<<<</d' 									~/.zshrc
	unalias rui 2>/dev/null
fi

if /usr/bin/grep -q "alias rui" ~/.bashrc; then
	echo "rui/scripts/install.sh: removing bash rui alias"
	sed -i '/# >>>>> RUI >>>>>/d' 									~/.bashrc
	sed -i '/# !! Contents within this block are managed by RUI/d' 	~/.bashrc
	sed -i '/alias rui=.*$/d'										~/.bashrc
	sed -i '/# <<<<< RUI <<<<</d' 									~/.bashrc
	unalias rui 2>/dev/null
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
~/python/bin/pipx install . --force
