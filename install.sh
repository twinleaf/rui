python3 -m venv $HOME/python
$HOME/python/bin/pip install twinleaf
$HOME/python/bin/pip install pyqt6

rui_alias="alias rui=\"$HOME/python/bin/python $( pwd )/rui.py\""
rc="$HOME/.$( basename $( readlink -f "/proc/$$/exe" ) )rc"
if ! cat "$rc" | grep -qe "^$rui_alias$"; then
	cat << EOF >> "$rc"

# >>>>> RUI >>>>>
# !! Contents within this block are managed by RUI
$rui_alias
# <<<<< RUI <<<<<
EOF
fi
