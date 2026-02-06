from itertools import cycle
from PyQt6.QtWidgets import QVBoxLayout, QComboBox, QCompleter, QLineEdit
from PyQt6.QtCore import Qt
from rui.guilib.style import qfont, generate_qss
from rui.lib.rpc import RPCList

class ToolBar:
    def __init__(self, rpc_full_list: RPCList):
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
        dropdown.setStyleSheet(generate_qss())
        dropdown.addItem("Select new rpc")
        dropdown.setFont(qfont())

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
        search_bar = CustomLineEdit(self.rpc_string)
        search_bar.setPlaceholderText("Search rpcs")
        search_bar.setCompleter(self.completer)
        return search_bar

class CustomLineEdit(QLineEdit):
    def __init__(self, items, parent = None):
        QLineEdit.__init__(self, parent)
        self.setFont(qfont())
        self.completion_items = items
        self.matches = cycle([item for item in self.completion_items if item.startswith(self.text())])
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
    
    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Tab:
            item = next(self.matches)
            self.setText(item)  
        else:
            self.matches = cycle([item for item in self.completion_items if item.startswith(self.text())]) 

        event.accept()
        QLineEdit.keyPressEvent(self, event)
