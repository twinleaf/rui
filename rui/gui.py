import sys, signal, subprocess
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout
from PyQt6.QtCore import Qt
from rui.guilib.toolbar import ToolBar
from rui.guilib.rpcdisplay import RPCDisplay
from rui.guilib.min_max import RuiConfigs
from rui.rpc import RPC, RPCList, RPCClient
from rui.cli import search_select

def gui(dev, args):
    """ RUI GUI main script """
    client = RPCClient(dev)
    slider_configs = RuiConfigs(client.dev_name())
    if args.terms:
        selected = search_select(client.list, args.terms, args.exact, args.all, args.multisearch)
    elif args.restore:
        selected = []
        for rpc in client.list: 
            if slider_configs.show_slider(rpc.name):
                selected.append(rpc)
    else:
        selected = []

    # Need to know which RPCs we can slide
    numeric_selected = RPCList([r for r in selected if r.is_numeric()])

    # If user selected a non-numeric RPC, tell them
    non_numeric = RPCList([r for r in selected if not r.is_numeric()])
    for rpc in non_numeric: print(f"{rpc} has type {rpc.arg_type}, can't make a slider")

    # Enable ctrl+C in terminal to exit
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    # Make app window
    app = QApplication([sys.argv[0]])
    window = MainWindow(client, slider_configs, numeric_selected)
    window.show()

    # make slider floating for i3wm, doesn't do anything if you're not Chris
    try: subprocess.run(["i3-msg", "floating", "toggle"], capture_output=True)
    except FileNotFoundError: pass

    sys.exit(app.exec()) 

class MainWindow(QWidget):
    """ RUI GUI main window class """
    def __init__(self, client: RPCClient, slider_configs: RuiConfigs, rpcs: RPCList):
        super().__init__()

        self.slider_configs = slider_configs 
        self.main_layout = QVBoxLayout()
        self.setLayout(self.main_layout)
        self.setWindowTitle('RUI GUI')
        self.setMinimumWidth(500)
        self.rpc_box = QWidget()
        self.rpc_layout = QVBoxLayout()
        self.rpc_layout.setSpacing(0)
        self.rpc_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignVCenter)
        self.rpc_list = RPCList([r for r in client.list if r.is_numeric()])

        self.tool_bar = ToolBar(self.rpc_list)
        self.tool_bar.completer.activated.connect(self.display_rpc_slider)
        self.tool_bar.returnPressed.connect(self.display_rpc_slider)
        self.rpcs_displayed = []

        self.rpc_box.setLayout(self.rpc_layout)
        self.main_layout.addLayout(self.tool_bar.menu, 1)
        self.main_layout.addWidget(self.rpc_box)
        for rpc in rpcs:
            min_val, max_val = self.get_rpc_min_max(rpc)
            new_rpc = RPCDisplay(rpc, min_val, max_val)
            self.rpc_layout.addLayout(new_rpc.grid_layout)
            self.rpc_layout.setSpacing(8)
            self.rpcs_displayed.append(new_rpc)

    def display_rpc_slider(self):
        """ Add a slider to display or show a hidden slider """
        if text := self.tool_bar.text():
            try: 
                index = self.tool_bar.rpc_names.index(text)
            except ValueError: 
                pass
            value = self.tool_bar.text()
            self.tool_bar.clearFocus()
            # check if rpc slider already displayed
            idx = next((i for i, rpc in enumerate(self.rpcs_displayed) if rpc.name == value), None)
            if idx is not None:
                if not self.rpcs_displayed[idx].widget_visible:
                    self.rpcs_displayed[idx].show_slider_box()
                self.rpcs_displayed[idx].slider.setFocus()
            elif value in self.tool_bar.rpc_names: #else make new slider
                min_val, max_val = self.get_rpc_min_max(self.rpc_list[index])
                self.slider_configs.update_displayed_rpcs(self.rpc_list[index].name, min_val, max_val, 1)
                new_rpc = RPCDisplay(self.rpc_list[index], min_val, max_val)
                self.rpc_layout.addLayout(new_rpc.grid_layout)
                self.rpc_layout.setSpacing(8)
                new_rpc.slider.setFocus()
                self.rpcs_displayed.append(new_rpc)

    def get_rpc_min_max(self, rpc):
        """ Get min/max values for RPC from slider config's cache """
        current_value = rpc.value()
        min_val = min(current_value, rpc.to_arg_type(self.slider_configs.get_rpc_min(rpc.name)))
        max_val = max(current_value, rpc.to_arg_type(self.slider_configs.get_rpc_max(rpc.name)))
        return min_val, max_val
    
    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.close()
        elif event.modifiers() == Qt.KeyboardModifier.ControlModifier and event.key() == Qt.Key.Key_W:
            self.close()
        elif event.text().isalpha():
            self.tool_bar.setFocus()
            self.tool_bar.setText(event.text())
        else:
            super().keyPressEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.RightButton or event.button() == Qt.MouseButton.LeftButton: 
            self.focusWidget().clearFocus() if self.focusWidget() else None

    def closeEvent(self, event):
        self.slider_configs.clear_visibility()
        for i, rpc in enumerate(self.rpcs_displayed): 
            if self.slider_configs.rpc_name_exists(rpc.name): 
                self.slider_configs.update_displayed_rpcs(rpc.name, rpc.min_label.text(), rpc.max_label.text(), rpc.widget_visible)
