import os, sys, subprocess
from typing import Callable
from client.lib.rpc import RPC, RPCList
from rpclib.rpclib import rpc_arg_type, rpc_ret_type

from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton
from PyQt6.QtWidgets import QSlider, QLabel, QLineEdit, QComboBox, QScrollArea, QCompleter, QGridLayout
from PyQt6.QtCore import Qt, QStringListModel
from PyQt6.QtGui import QFont, QDoubleValidator, QIcon
import random # for colors

def slider(full_list: RPCList, selected: RPCList, fork: bool=True):

    # Need to know which RPCs we can slide
    numeric_full = RPCList([r for r in full_list if r.arg_type in {int, float}])
    numeric_selected= RPCList([r for r in selected if r.arg_type in {int, float}])

    # If user selected a non-numeric RPC, tell them
    non_numeric = RPCList([r for r in selected if r.arg_type not in {int, float}])
    for rpc in non_numeric: print(f"{rpc} has type {rpc.arg_type}, can't make a slider")

    # See which rpcs we need to watch out for changes behind our backs
    for rpc in numeric_selected: rpc.check_is_sample()

    if numeric_selected.empty(): sys.exit("No rpcs to slide!")

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

        self.main_layout = QVBoxLayout()
        self.setLayout(self.main_layout)  
        self.main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.setWindowTitle('RUI GUI')
        self.setMinimumWidth(500)
        self.rpc_box = QWidget()
        self.rpc_layout = QVBoxLayout() 
        self.rpc_layout.setSpacing(0)
        self.rpc_list = rpc_full_list 

        self.tool_bar = ToolBar(rpc_full_list)
        self.tool_bar.dropdown.activated.connect(lambda: self.display_rpc_slider("drop"))
        self.tool_bar.completer.activated.connect(lambda: self.display_rpc_slider("search"))
        self.rpcs_displayed = [0]
        
        for rpc in rpcs:
            try: min_val = RPC(rpc.name+'.min', rpc.arg_type).call()
            except RuntimeError: min_val = 0
            try: max_val = RPC(rpc.name+'.max', rpc.arg_type).call()
            except RuntimeError: max_val = rpc.call()

            self.display = MakeRPCDisplay(rpc, min_val, max_val)
            self.rpc_layout.addLayout(self.display.grid_layout, 1)
            self.rpcs_displayed.append(self.display)
        
        self.rpc_box.setLayout(self.rpc_layout)
        self.main_layout.addLayout(self.tool_bar.menu, 1)
        self.main_layout.addWidget(self.rpc_box)

    def display_rpc_slider(self, selection_type): 
        match selection_type:
            case "drop": 
                index = self.tool_bar.dropdown.currentIndex()
                value = self.tool_bar.dropdown.currentText()

            case "search": 
                index = self.tool_bar.dropdown.findText(self.tool_bar.search_bar.text())
                value = self.tool_bar.search_bar.text()
            case _: index = 0

        if index:
                #check if rpc slider already displayed
                idx = next((i + 1 for i, rpc in enumerate(self.rpcs_displayed[1:]) if rpc.name == value), None)
                if idx:
                    if not self.rpcs_displayed[idx].widget_visible:
                        self.rpcs_displayed[idx].show_slider_box()
                else: #else make new slider
                    new_rpc = MakeRPCDisplay(self.rpc_list[index-1], 0, self.rpc_list[index-1].call())
                    self.rpcs_displayed.append(new_rpc)
                    self.rpc_layout.addLayout(new_rpc.grid_layout)
    
class ToolBar():
    def __init__(self, rpc_full_list):
        self.rpc_list = rpc_full_list
        self.rpc_string = []
        self.menu = QVBoxLayout()

        self.dropdown = self.make_dropdown()
        self.completer = self.make_completer()
        self.search_bar = self.make_searchbar()

        self.menu.addWidget(self.search_bar)
        self.menu.addWidget(self.dropdown)
    
    def make_dropdown(self) -> QComboBox:
        dropdown = QComboBox()
        dropdown.adjustSize()
        dropdown.setStyleSheet(_generate_qss())
        dropdown.addItem("Select new rpc")

        for rpc in self.rpc_list:
            dropdown.addItem(rpc.name)
            self.rpc_string.append(rpc.name)
        return dropdown
    
    def make_completer(self) -> QCompleter:
        completer = QCompleter(self.rpc_string)
        completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        completer.setFilterMode(Qt.MatchFlag.MatchContains)
        completer.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
        return completer

    def make_searchbar(self) -> QLineEdit:
        search_bar = QLineEdit()
        search_bar.setPlaceholderText("Search rpcs")
        search_bar.setCompleter(self.completer)
        #search_bar.selectionChanged.connect(self.tab_completion) //TODO: Functional tab completion
        return search_bar

    def tab_completion(self, event):
        if event.key() == Qt.Key.Key_Tab and self.completer.popup().isVisible():
            self.completer.insertCompletion(self.completer.currentCompletion()) 
            return

class MakeRPCDisplay():
    def __init__(self, rpc: RPC, min_val: rpc_ret_type, max_val: rpc_ret_type):
        self.rpc = rpc
        self.scale = 100 if rpc.arg_type == float else 1
        self.__get_value()

        self.widget_visible = True
        self.name = rpc.name
        self.name_label = self.make_label(rpc.name)
        self.result_label = self.make_label(self.__result_display())
        self.delete_button = self.make_button()
        self.slider = self.make_slider(min_val, max_val)
        self.min_label = self.make_edit(str(min_val), self.slider.setMinimum)
        self.max_label = self.make_edit(str(max_val), self.slider.setMaximum)

        self.grid_layout = QGridLayout()
        self.grid_layout.setSpacing(0)
        self.grid_layout.addWidget(self.name_label, 0, 0)
        self.grid_layout.addWidget(self.result_label, 0, 1, alignment= Qt.AlignmentFlag.AlignHCenter)
        self.grid_layout.addWidget(self.delete_button, 0, 2, alignment =Qt.AlignmentFlag.AlignLeft)
        self.grid_layout.addWidget(self.min_label, 1, 0)
        self.grid_layout.addWidget(self.slider, 1, 1)
        self.grid_layout.addWidget(self.max_label, 1, 2, alignment= Qt.AlignmentFlag.AlignLeft)

    def make_label(self, name) -> QLabel:
        label = QLabel(name)
        label.setFont(self.__qfont())
        return label

    def make_edit(self, default: str, edit_func: Callable[[int], None]) -> QLineEdit:
        edit = QLineEdit()
        edit.setText(default)
        edit.setFont(self.__qfont())
        edit.setFixedWidth(50)
        edit.setValidator(QDoubleValidator())
        edit.setStyleSheet(_generate_qss())
        edit.returnPressed.connect(lambda: edit_func(self.__scale(edit.text())))
        return edit

    def make_slider(self, min_val: rpc_ret_type, max_val: rpc_ret_type) -> QSlider:
        self.updating = False
        slider = QSlider(Qt.Orientation.Horizontal)
        slider.setRange(self.__scale(min_val), self.__scale(max_val))
        slider.setValue(self.value_scaled)
        slider.setSingleStep(1)
        slider.setPageStep(10)
        slider.setStyleSheet(_generate_qss())
        slider.valueChanged.connect(self.update_slider)
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
        button = QPushButton()
        icon = QIcon().fromTheme("edit-delete")
        button.setIcon(icon)
        button.setStyleSheet(_generate_qss())
        if (self.widget_visible == True):
            button.clicked.connect(self.hide_slider_box)
        return button

    def hide_slider_box(self):
        self.grid_layout.removeWidget(self.name_label)
        self.grid_layout.removeWidget(self.result_label)
        self.grid_layout.removeWidget(self.delete_button)
        self.grid_layout.removeWidget(self.min_label)
        self.grid_layout.removeWidget(self.slider)
        self.grid_layout.removeWidget(self.max_label)
        self.name_label.hide()
        self.result_label.hide()
        self.delete_button.hide()
        self.slider.hide()
        self.min_label.hide()
        self.max_label.hide()
        self.widget_visible = False
    
    def show_slider_box(self):
        self.name_label.show()
        self.result_label.show()
        self.delete_button.show()
        self.slider.show()
        self.min_label.show()
        self.max_label.show() 
        self.grid_layout.addWidget(self.name_label)
        self.grid_layout.addWidget(self.result_label)
        self.grid_layout.addWidget(self.delete_button)
        self.grid_layout.addWidget(self.min_label)
        self.grid_layout.addWidget(self.slider)
        self.grid_layout.addWidget(self.max_label)
        self.widget_visible = True

    def __get_value(self):
        self.value = self.rpc.value()
        self.value_scaled = self.__scale(self.value)
    def __result_display(self): return f"Current value: {self.value}"
    def __qfont(self, size: int=14): return QFont('Ubuntu', size)

    def __scale(self, val: rpc_ret_type ) -> int:
        return round(self.rpc.arg_type(val) * self.scale)
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
        border-radius: 5px;
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

    QPushButton {{
        background-color: transparent;
        color: red;
    }}

    QLineEdit {{
        border: 1px solid #5c5c5c;
        border-radius: 9px;
    }}
    """

def _random_hex(total: int) -> str:
    ret = "#"
    for i in range(3):
        max = 255 if total > 255 else total
        r = random.randint(0, max)
        ret += hex(r)[2:].zfill(2)
    return ret
