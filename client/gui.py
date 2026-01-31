# TODO: use multiprocessing instead of os.fork
import os, sys, subprocess, multiprocessing
from typing import Callable
from rpclib.rpc import RPC, RPCList
from rpclib.rpctypes import rpc_arg_type, rpc_ret_type

from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton
from PyQt6.QtWidgets import QSlider, QLabel, QLineEdit, QComboBox, QCheckBox
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QDoubleValidator
import random # for colors

def slider(full_list: RPCList, selected: RPCList, fork: bool=True):

    # Need to know which RPCs we can slide
    numeric_full = RPCList([r for r in full_list if r.arg_type in {int, float}])
    numeric_selected= RPCList([r for r in selected if r.arg_type in {int, float}])

    # If user selected a non-numeric RPC, tell them
    non_numeric = RPCList([r for r in selected if r.arg_type not in {int, float}])
    for rpc in non_numeric: print(f"{rpc} has type {rpc.arg_type}, can't make a slider")

    # See which rpcs we need to watch out for changes behind our backs
    for rpc in numeric: rpc.check_is_sample()

    if rpcs.empty(): sys.exit("No rpcs to slide!")

    if fork:
        pid = os.fork()         # we use fork to keep child alive after parent ends
        if pid > 0: sys.exit()  # we're a parent, exit
        os.setsid()             # detach from terminal
        sys.stdin.close()       # close streams
        sys.stdout.close()
        sys.stderr.close()

    app = QApplication([sys.argv[0]])
    window = MainWindow(numeric_selected, numeric_full)
    window.show()

    # make slider floating for i3wm, doesn't do anything if you're not Chris
    try: subprocess.run(["i3-msg", "floating", "toggle"], capture_output=True)
    except FileNotFoundError: pass

    sys.exit(app.exec())

class MainWindow(QWidget):
    def __init__(self, rpcs: RPCList, rpc_full_list):
        super().__init__()

        self.layout = QVBoxLayout()
        self.setLayout(self.layout)
        self.layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignCenter)
        self.setWindowTitle('findrpc GUI')
        self.setMinimumWidth(500)

        self.rpcs_displayed = [0]
        self.dropdown = QComboBox()
        self.dropdown.setStyleSheet(_generate_qss())
        self.dropdown.addItem("Select new rpc")
        
        self.rpc_list = rpc_full_list
        for rpc in self.rpc_list:
            self.dropdown.addItem(rpc.name)
        self.layout.addWidget(self.dropdown)

        for rpc in rpcs:
            try: min_val = RPC(rpc.name+'.min', rpc.arg_type).call()
            except RuntimeError: min_val = 0
            try: max_val = RPC(rpc.name+'.max', rpc.arg_type).call()
            except RuntimeError: max_val = rpc.call()

            self.display = RPCDisplay(rpc, min_val, max_val)
            self.layout.addLayout(self.display.label_container)
            self.layout.addLayout(self.display.slider_container)

            self.rpcs_displayed.append(self.display)

        self.dropdown.activated.connect(self.display_rpc_slider)

    def display_rpc_slider(self):
        index = self.dropdown.currentIndex()
        dropdown_value = self.dropdown.currentText()
        if index:
                idx = next((i + 1 for i, rpc in enumerate(self.rpcs_displayed[1:]) if rpc.name == dropdown_value), None)
                if idx:
                    if not self.rpcs_displayed[idx].widget_visible:
                        self.rpcs_displayed[idx].show_slider()
                        self.rpcs_displayed[idx].widget_visible = True
                else:
                    new_rpc = RPCDisplay(self.rpc_list[index-1], 0, self.rpc_list[index-1].call())
                    self.rpcs_displayed.append(new_rpc)
                    self.layout.addLayout(new_rpc.label_container)
                    self.layout.addLayout(new_rpc.slider_container)

class RPCDisplay():
    def __init__(self, rpc: RPC, min_val: rpc_ret_type, max_val: rpc_ret_type):
        self.rpc = rpc
        self.scale = 100 if rpc.arg_type == float else 1
        self.__get_value()

        self.widget_visible = True
        self.name = rpc.name
        self.name_label = self.make_label(rpc.name)
        self.result_label = self.make_label(self.__result_display())
        self.delete_button = self.make_button()

        self.label_container = QHBoxLayout()
        self.label_container.addWidget(self.name_label)
        self.label_container.addWidget(self.result_label)
        self.label_container.addWidget(self.delete_button)
        
        self.slider = self.make_slider(min_val, max_val)
        self.min_label = self.make_edit(str(min_val), self.slider.setMinimum)
        self.max_label = self.make_edit(str(max_val), self.slider.setMaximum)

        self.slider_container = QHBoxLayout()
        self.slider_container.addWidget(self.min_label)
        self.slider_container.addWidget(self.delete_button)
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

            value_real = self.__descale(value)
            self.rpc.call(value_real)
            self.__get_value()

            self.result_label.setText(self.__result_display())
            self.slider.setValue(self.value_scaled)
            self.updating = False

    def make_button(self):
        button = QPushButton("Delete")
        button.setFixedSize(50, 40)
        button.adjustSize()
        if (self.widget_visible == True):
            button.clicked.connect(self.hide_slider)
            self.widget_visible = False
        return button

    def hide_slider(self):
        self.label_container.removeWidget(self.name_label)
        self.label_container.removeWidget(self.result_label)
        self.label_container.removeWidget(self.delete_button)
        self.slider_container.removeWidget(self.min_label)
        self.slider_container.removeWidget(self.slider)
        self.slider_container.removeWidget(self.max_label)
        self.name_label.hide()
        self.result_label.hide()
        self.delete_button.hide()
        self.slider.hide()
        self.min_label.hide()
        self.max_label.hide()
        self.label_container.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignCenter) 
        self.slider_container.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignCenter)
    
    def show_slider(self):
        self.label_container.addWidget(self.name_label)
        self.label_container.addWidget(self.result_label)
        self.label_container.addWidget(self.delete_button)
        self.slider_container.addWidget(self.min_label)
        self.slider_container.addWidget(self.slider)
        self.slider_container.addWidget(self.max_label)
        self.name_label.show()
        self.result_label.show()
        self.delete_button.show()
        self.slider.show()
        self.min_label.show()
        self.max_label.show() 

    def __get_value(self):
        self.value = self.rpc.value()
        self.value_scaled = self.__scale(self.value)
    def __result_display(self): return f"Current value: {self.value}"
    def __qfont(self, size: int=14): return QFont('Ubuntu', size)
    def __scale(self, val: rpc_ret_type ) -> int:
        return int(self.rpc.arg_type(val) * self.scale)
    def __descale(self, val: int) -> rpc_arg_type:
        return self.rpc.arg_type(val / self.scale)

def _generate_qss() -> str:
    return f"""
    QComboBox {{
        border: 2px solid grey;
        border-radius: 5px;
        min-width: 6em;
        color:black;
        background-color:white;}}
    QComboBox:hover{{background-color:lightgrey}}

    QComboBox QAbstractItemView{{
        border-color:2px solid black;
        border-radius: 3px;
        color:white;
        selection-background-color:lightgrey}}

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
