import os, sys, subprocess
from rpc import RPC
from rpcio import arg_input

from PyQt6.QtWidgets import QApplication, QWidget, QSlider, QLabel, QVBoxLayout, QHBoxLayout
from PyQt6.QtCore import Qt, QRect
from PyQt6.QtGui import QFont

def slider(rpc: RPC, fork=True):
    try: min_val = RPC(rpc.name+'.min', rpc.type_ext).value()
    except RuntimeError: min_val = arg_input(rpc, prompt="min value")
    try: max_val = RPC(rpc.name+'.max', rpc.type_ext).value()
    except RuntimeError: max_val = arg_input(rpc, prompt="max value")

    if fork:
        pid = os.fork()
        if pid > 0: return      # we're a parent, go back to main
        os.setsid()             # detach from terminal
        sys.stdin.close()       # close streams
        sys.stdout.close()
        sys.stderr.close()

    app = QApplication([sys.argv[0]])
    window = MainWindow(rpc, min_val, max_val)
    window.show()

    # make slider floating for i3wm
    try: subprocess.run(["i3-msg", "floating", "toggle"], capture_output=True)
    except FileNotFoundError: pass  

    sys.exit(app.exec())

class MainWindow(QWidget):
    def __init__(self, rpc: RPC, min_val: float, max_val: float):
        super().__init__()
        self.rpc = rpc

        layout = QVBoxLayout()
        self.setLayout(layout)
        self.setWindowTitle(rpc.name)
        self.setMinimumWidth(500)
        self.qfont = QFont('Ubuntu', 16)

        self.slider, self.container = self.__make_slider(min_val, max_val)
        self.name_label = self.__make_label(self.rpc.name)
        self.result_label = self.__make_label(RESULT_LABEL(self.value))

        layout.addWidget(self.name_label)
        layout.addLayout(self.container)
        layout.addWidget(self.result_label)

    def __make_slider(self, min_val, max_val):
        min_label = QLabel(str(min_val), self)
        min_label.setFont(self.qfont)
        max_label = QLabel(str(max_val), self)
        max_label.setFont(self.qfont)

        self.updating = False
        self.__get_value()
        slider = QSlider(Qt.Orientation.Horizontal, self)
        slider.setRange(_scale(min_val), _scale(max_val))
        slider.setValue(_scale(self.value))
        slider.setSingleStep(1)
        slider.setPageStep(10)
        slider.valueChanged.connect(self.__update)
        slider.setStyleSheet(SLIDER_QSS)

        container = QHBoxLayout()
        container.addWidget(min_label)
        container.addWidget(slider)
        container.addWidget(max_label)

        return slider, container

    def __update(self, value: int):
        if not self.updating: # don't recursively call this
            self.updating = True
            self.rpc.call(_descale(value))
            self.__get_value()
            self.result_label.setText(RESULT_LABEL(self.value))
            self.slider.setValue(_scale(self.value))
            self.updating = False

    def __make_label(self, name):
        label = QLabel(name, self)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setFont(self.qfont)
        label.adjustSize()
        return label

    def __get_value(self):
        self.value = self.rpc.value()

SLIDER_QSS="""
        QSlider::groove:horizontal {
            border: 3px solid #999999;
            height: 8px; /* the groove height */
            background: #e0e0e0;
            margin: 2px 0;
            border-radius: 4px;
        }

        QSlider::handle:horizontal {
            background: #1de9b6; /* a cyan color */
            border: 3px solid #5c5c5c;
            width: 18px;
            height: 18px;
            margin: -6px 0; /* center the handle vertically within the groove */
            border-radius: 9px; /* makes the handle circular */
        }

        QSlider::add-page:horizontal {
            background: #b0b0b0; /* color for the part after the handle */
        }

        QSlider::sub-page:horizontal {
            background: #1dc996; /* color for the part before the handle */
        }
        """

SCALE = 100
RESULT_LABEL = lambda x: f'Current value: {x}'
def _scale(val: float | str) -> int:
    return int(float(val) * SCALE)
def _descale(val: int) -> str:
    return str(float(val) / SCALE)
