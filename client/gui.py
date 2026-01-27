# TODO: if we have the speed, fetch value at intervals i/s/o every call (value cache)
import os, sys, subprocess, random
from typing import Callable
from rpclib.rpc import RPC, RPCList
from rpclib.rpctypes import rpc_arg_type, rpc_ret_type

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
            try: min_val = RPC(rpc.name+'.min', rpc.arg_type).call()
            except RuntimeError: min_val = 0
            try: max_val = RPC(rpc.name+'.max', rpc.arg_type).call()
            except RuntimeError: max_val = rpc.call()

            display = RPCDisplay(rpc, min_val, max_val)
            layout.addLayout(display.label_container)
            layout.addLayout(display.slider_container)
            layout.addStretch()

class RPCDisplay():
    def __init__(self, rpc: RPC, min_val: rpc_ret_type, max_val: rpc_ret_type):
        self.rpc = rpc
        self.scale = 100 if rpc.arg_type == float else 1
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

    def make_slider(self, min_val: rpc_ret_type, max_val: rpc_ret_type) -> QSlider:
        self.updating = False
        slider = QSlider(Qt.Orientation.Horizontal)
        slider.setRange(self.__scale(min_val), self.__scale(max_val))
        slider.setValue(self.value_scaled)
        slider.setSingleStep(1)
        slider.setPageStep(10)
        slider.valueChanged.connect(self.update_slider)
        slider.setStyleSheet(_generate_qss())

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
        self.value = self.rpc.call()
        self.value_scaled = self.__scale(self.value)
    def __result_display(self): return f"Current value: {self.value}"
    def __qfont(self, size: int=14): return QFont('Ubuntu', size)
    def __scale(self, val: rpc_ret_type ) -> int:
        assert self.rpc.arg_type in {int, float} # for mypy, will never fail probably
        return int(self.rpc.arg_type(val) * self.scale)
    def __descale(self, val: int) -> rpc_arg_type:
        assert self.rpc.arg_type in {int, float} # for mypy
        return self.rpc.arg_type(val / self.scale)

def _generate_qss() -> str:
    return f"""
    QSlider::groove:horizontal {{
        border: 3px solid #999999;
        height: 8px; /* the groove height */
        background: #e0e0e0;
        margin: 2px 0;
        border-radius: 4px;
    }}

    QSlider::handle:horizontal {{
        background: #ffffff;
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
        background: {_random_hex(500)}; /* color for the part before the handle */
    }}
    """

def _random_hex(total: int) -> str:
    ret = "#"
    for i in range(3):
        max = 255 if total > 255 else total
        r = random.randint(0, max)
        ret += hex(r)[2:].zfill(2)
    return ret
