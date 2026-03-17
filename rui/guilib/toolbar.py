from itertools import cycle
from PyQt6.QtWidgets import QVBoxLayout, QComboBox, QCompleter, QLineEdit
from PyQt6.QtCore import Qt
from rui.guilib.style import qfont 

class ToolBar(QLineEdit):
    def __init__(self, rpc_full_list, parent = None):
        QLineEdit.__init__(self, parent)
        self.setFont(qfont())
        self.rpc_names =[]
        for rpc in rpc_full_list: self.rpc_names.append(rpc.name)
        self.completion_items = self.rpc_names
        self.matches = cycle([item for item in self.completion_items if item.startswith(self.text())])

        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.completer = CustomCompleter(self.completion_items)
        self.setCompleter(self.completer)
        self.setPlaceholderText("Search rpcs")

        self.menu = QVBoxLayout()
        self.menu.addWidget(self)

    def keyPressEvent(self, event):
        self.matches = cycle([item for item in self.completion_items if item.startswith(self.text())])
        event.accept()
        QLineEdit.keyPressEvent(self, event)

class CustomCompleter(QCompleter):
    def __init__(self, rpc_names, parent=None):
        QCompleter.__init__(self, rpc_names, parent)
        self.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.setFilterMode(Qt.MatchFlag.MatchContains)
        self.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
