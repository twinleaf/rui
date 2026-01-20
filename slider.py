import os, sys, subprocess, random
from typing import Callable
from rpc import RPC
from rpclist import RPCList
from rpcio import arg_input

from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout
from PyQt6.QtWidgets import QSlider, QLabel, QLineEdit
from PyQt6.QtCore import Qt, QRect
from PyQt6.QtGui import QFont, QDoubleValidator

def slider(rpcs: RPCList, fork=True):
    if fork:
        pid = os.fork()
        if pid > 0: sys.exit()  # we're a parent, exit
        os.setsid()             # detach from terminal
        sys.stdin.close()       # close streams
        sys.stdout.close()
        sys.stderr.close()

    app = QApplication([sys.argv[0]])
    window = MainWindow(rpcs)
    window.show()

    # make slider floating for i3wm
    try: subprocess.run(["i3-msg", "floating", "toggle"], capture_output=True)
    except FileNotFoundError: pass  

    sys.exit(app.exec())

class MainWindow(QWidget):
    def __init__(self, rpcs: RPCList):
        super().__init__()

        layout = QVBoxLayout()
        layout.addStretch()
        self.setLayout(layout)
        self.setWindowTitle('findrpc GUI')
        self.setMinimumWidth(500)

        for rpc in rpcs:
            try: min_val = RPC(rpc.name+'.min', rpc.type_ext).value()
            except RuntimeError: min_val = 0 #arg_input(rpc, prompt="min value")
            try: max_val = RPC(rpc.name+'.max', rpc.type_ext).value()
            except RuntimeError: max_val = rpc.value() #arg_input(rpc, prompt="max value")

            display = RPCDisplay(rpc, min_val, max_val)
            layout.addLayout(display.label_container)
            layout.addLayout(display.slider_container)
            layout.addStretch()

class RPCDisplay():
    def __init__(self, rpc: RPC, min_val: float | int, max_val: float | int):
        self.rpc = rpc
        self.scale = 100 if rpc.data_type == float else 1
        self.__get_value()

        self.name_label = self.make_label(rpc.name)
        self.result_label = self.make_label(self.__result_display())

        self.label_container = QHBoxLayout()
        self.label_container.addWidget(self.name_label)
        self.label_container.addWidget(self.result_label)

        self.slider = self.make_slider(min_val, max_val)
        self.min_label = self.make_edit(str(min_val), self.slider.setMinimum)
        self.max_label = self.make_edit(str(max_val), self.slider.setMaximum)

        self.slider_container = QHBoxLayout()
        self.slider_container.addWidget(self.min_label)
        self.slider_container.addWidget(self.slider)
        self.slider_container.addWidget(self.max_label)

    def make_label(self, name) -> QLabel:
        label = QLabel(name)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setFont(self.__qfont())
        label.adjustSize()
        return label

    def make_edit(self, default: str, edit_func: Callable[[int], None]) -> QLineEdit:
        edit = QLineEdit()
        edit.setText(default)
        edit.setFont(self.__qfont())
        edit.adjustSize()
        edit.setFixedWidth(50)
        edit.setValidator(QDoubleValidator())
        edit.returnPressed.connect(lambda: edit_func(self.__scale(edit.text())))
        return edit

    def make_slider(self, min_val: float | int, max_val: float | int) -> QSlider:
        r, g, b = (_random_hex(128,160) for _ in range(3))
        slider_color = f'#{r}{g}{b}'
        r, g, b = (_random_hex(0,128) for _ in range(3))
        handle_color = f'#{r}{g}{b}'

        self.updating = False
        slider = QSlider(Qt.Orientation.Horizontal)
        slider.setRange(self.__scale(min_val), self.__scale(max_val))
        slider.setValue(self.value_scaled)
        slider.setSingleStep(1)
        slider.setPageStep(10)
        slider.valueChanged.connect(self.update_slider)
        slider.setStyleSheet(_generate_qss(slider_color, handle_color))

        return slider

    def update_slider(self, value: int):
        if not self.updating: # don't recursively call this
            self.updating = True
            self.rpc.call(self.__descale(value))
            self.__get_value()
            self.result_label.setText(self.__result_display())
            self.slider.setValue(self.value_scaled)
            self.updating = False

    def __get_value(self): 
        self.value = self.rpc.value()
        self.value_scaled = self.__scale(self.value)
    def __result_display(self): return f"Current value: {self.value}"
    def __qfont(self, size: int=14): return QFont('Ubuntu', size)
    def __scale(self, val: float | int | str) -> int:
        if self.rpc.data_type not in {float, int}:
            raise TypeError('Data type for slider must be numeric')
        return int(self.rpc.data_type(val) * self.scale)
    def __descale(self, val: int) -> str:
        if self.rpc.data_type not in {float, int}:
            raise TypeError('Data type for slider must be numeric')
        return str(self.rpc.data_type(val / self.scale))

def _generate_qss(slider_color: str, handle_color: str) -> str:
    return f"""
    QSlider::groove:horizontal {{
        border: 3px solid #999999;
        height: 8px; /* the groove height */
        background: #e0e0e0;
        margin: 2px 0;
        border-radius: 4px;
    }}

    QSlider::handle:horizontal {{
        background: {handle_color};
        border: 3px solid #5c5c5c;
        width: 18px;
        height: 18px;
        margin: -6px 0; /* center the handle vertically within the groove */
        border-radius: 9px; /* makes the handle circular */
    }}

    QSlider::add-page:horizontal {{
        background: #b0b0b0; /* color for the part after the handle */
    }}

    QSlider::sub-page:horizontal {{
        background: {slider_color}; /* color for the part before the handle */
    }}
    """

def _random_hex(min: int, max:int) -> str:
    return hex(random.randint(128,160))[2:].zfill(2)
