from itertools import cycle

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QComboBox, QCompleter, QLineEdit, QVBoxLayout

from rui.app.guilib.style import qfont


class ToolBar(QLineEdit):
    def __init__(self, rpc_full_list, parent=None):
        QLineEdit.__init__(self, parent)
        self.setFont(qfont())

        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.rpc_names = [r.name for r in rpc_full_list]
        self.completer = CustomCompleter(self.rpc_names)
        self.setCompleter(self.completer)
        self.setPlaceholderText("Search rpcs")

        self.menu = QVBoxLayout()
        self.menu.addWidget(self)

    def mousePressEvent(self, event):
        self.completer.setCompletionPrefix("")
        self.completer.complete()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.clearFocus()
        else:
            event.accept()
            QLineEdit.keyPressEvent(self, event)


class CustomCompleter(QCompleter):
    def __init__(self, rpc_names, parent=None):
        QCompleter.__init__(self, rpc_names, parent)
        self.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.setFilterMode(Qt.MatchFlag.MatchContains)
        self.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
        self.popup().setFocusPolicy(Qt.FocusPolicy.StrongFocus)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Tab:
            self.popup.setFocus()
            cur_index = self.currentRow()
            if cur_index is None:
                cur_index = 0
            self.setCurrentRow(cur_index + 1)
        elif event.key() == Qt.Key.Key_Escape:
            self.popup.clearFocus()
