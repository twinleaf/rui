# source install.sh to set up rui for bash or zsh
# currently no support for any other shell that don't conveniently use ~/.*shrc

if ! [ -d $HOME/python ]; then
	echo "python3 -m venv $HOME/python ..."
	python3 -m venv $HOME/python
fi
$HOME/python/bin/pip install twinleaf
$HOME/python/bin/pip install pyqt6

rui_alias="$HOME/python/bin/python $( pwd )/rui.py"
rc="$HOME/.$( ps cp "$$" -o command= )rc"
if ! cat "$rc" | grep -qe "$rui_alias"; then
	cat << EOF >> "$rc"

# >>>>> RUI >>>>>
# !! Contents within this block are managed by RUI
alias rui="$rui_alias"
# <<<<< RUI <<<<<
EOF
fi

# enable alias in this shell
alias rui="$rui_alias"
