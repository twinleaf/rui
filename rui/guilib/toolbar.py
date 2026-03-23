from itertools import cycle
from PyQt6.QtWidgets import QVBoxLayout, QComboBox, QCompleter, QLineEdit
from PyQt6.QtCore import Qt
from rui.guilib.style import qfont 

class ToolBar(QLineEdit):
    def __init__(self, rpc_full_list, parent = None):
        QLineEdit.__init__(self, parent)
        self.setFont(qfont())

        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.rpc_names = [r.name for r in rpc_full_list]
        self.completer = CustomCompleter(self.rpc_names)
        self.setCompleter(self.completer)
        self.setPlaceholderText("Search rpcs")

        self.menu = QVBoxLayout()
        self.menu.addWidget(self)

    def keyPressEvent(self, event):
        event.accept()
        QLineEdit.keyPressEvent(self, event)

class CustomCompleter(QCompleter):
    def __init__(self, rpc_names, parent=None):
        QCompleter.__init__(self, rpc_names, parent)
        self.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.setFilterMode(Qt.MatchFlag.MatchContains)
        self.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
