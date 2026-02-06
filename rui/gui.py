import sys, subprocess
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout
from PyQt6.QtCore import Qt
from rui.guilib.toolbar import ToolBar
from rui.guilib.rpcdisplay import RPCDisplay

from rui.lib.rpc import RPCList

def slider(full_list: RPCList, selected: RPCList):
    # Need to know which RPCs we can slide
    numeric_full = RPCList([r for r in full_list if r.arg_type in {int, float}])
    numeric_selected= RPCList([r for r in selected if r.arg_type in {int, float}])

    # If user selected a non-numeric RPC, tell them
    non_numeric = RPCList([r for r in selected if r.arg_type not in {int, float}])
    for rpc in non_numeric: print(f"{rpc} has type {rpc.arg_type}, can't make a slider")

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
        #self.main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.setWindowTitle('RUI GUI')
        self.setMinimumWidth(500)
        self.rpc_box = QWidget()
        self.rpc_layout = QVBoxLayout()
        self.rpc_layout.setSpacing(0)
        self.rpc_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignVCenter)
        self.rpc_list = rpc_full_list 

        self.tool_bar = ToolBar(rpc_full_list)
        self.tool_bar.dropdown.activated.connect(lambda: self.display_rpc_slider("drop"))
        self.tool_bar.completer.activated.connect(lambda: self.display_rpc_slider("search"))
        self.tool_bar.search_bar.returnPressed.connect(lambda: self.display_rpc_slider("search"))
        self.rpcs_displayed = [0]
        
        self.rpc_box.setLayout(self.rpc_layout)
        self.main_layout.addLayout(self.tool_bar.menu, 1)
        self.main_layout.addWidget(self.rpc_box)

        for rpc in rpcs:
            try: min_val = rpc._node.min()
            except AttributeError: min_val = 0
            try: max_val = rpc._node.max()
            except AttributeError: max_val = rpc.call()

            self.display = RPCDisplay(rpc, min_val, max_val)
            self.rpc_layout.addLayout(self.display.grid_layout)
            self.rpc_layout.setSpacing(8)
            self.rpcs_displayed.append(self.display)

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
                elif value in self.tool_bar.rpc_string: #else make new slider
                    new_rpc = RPCDisplay(self.rpc_list[index-1], 0, self.rpc_list[index-1].call())
                    self.rpc_layout.addLayout(new_rpc.grid_layout)
                    self.rpc_layout.setSpacing(8)
                    self.rpcs_displayed.append(new_rpc)
