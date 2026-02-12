python3 -m venv $HOME/python
$HOME/python/bin/pip install twinleaf
$HOME/python/bin/pip install pyqt6
echo "alias rui=\"$( pwd )/rui.py\"" >> $HOME/.$( basename $0 )rc
