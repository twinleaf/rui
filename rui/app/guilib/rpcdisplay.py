from pathlib import Path

from PyQt6.QtCore import QSize, Qt
from PyQt6.QtGui import QDoubleValidator, QIcon
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSlider,
    QVBoxLayout,
)

from rui.app.guilib.min_max import RuiConfigs
from rui.app.guilib.style import generate_qss, qfont
from rui.lib.client import PROXY_FATAL, RPC_ERROR
from rui.lib.rpc import RPC


class RPCDisplay:
    """Display for a single RPC slider, including name, min/max, and current value"""

    def __init__(self, rpc: RPC, min_val: int | float, max_val: int | float):
        self.name = rpc.name
        self.widget_visible = 1
        self.slider = RPCSlider(rpc, min_val, max_val)
        self.name_label = RPCLabel(self.name)
        self.result_label = RPCLabel(self.__result_display())
        self.min_label = EditBox(str(min_val))
        self.max_label = EditBox(str(max_val))
        self.delete_button = RPCButton()

        self.delete_button.clicked.connect(
            lambda: self.hide_slider_box() if self.widget_visible else None
        )
        self.slider.valueChanged.connect(
            lambda: self.result_label.setText(self.__result_display())
        )
        self.min_label.returnPressed.connect(
            lambda: self.slider.setMinimum(self.slider.scale(self.min_label.text()))
        )
        self.max_label.returnPressed.connect(
            lambda: self.slider.setMaximum(self.slider.scale(self.max_label.text()))
        )
        self.min_label.returnPressed.connect(lambda: self.slider.setFocus())
        self.max_label.returnPressed.connect(lambda: self.slider.setFocus())
        self.setup_layout()

    def setup_layout(self):
        self.grid_layout = QVBoxLayout()
        self.first_row = QHBoxLayout()
        self.second_row = QHBoxLayout()
        self.second_row.setSpacing(8)
        self.first_row.addWidget(self.name_label)
        self.first_row.addWidget(
            self.result_label, alignment=Qt.AlignmentFlag.AlignHCenter
        )
        self.first_row.addWidget(
            self.delete_button, alignment=Qt.AlignmentFlag.AlignRight
        )
        self.second_row.addWidget(self.min_label)
        self.second_row.addWidget(self.slider)
        self.second_row.addWidget(self.max_label)
        self.grid_layout.addLayout(self.first_row)
        self.grid_layout.addLayout(self.second_row)
        if self.widget_visible == 0:
            self.hide_slider_box()

    def hide_slider_box(self):
        self.first_row.removeWidget(self.name_label)
        self.first_row.removeWidget(self.result_label)
        self.first_row.removeWidget(self.delete_button)
        self.second_row.removeWidget(self.min_label)
        self.second_row.removeWidget(self.slider)
        self.second_row.removeWidget(self.max_label)
        self.name_label.hide()
        self.result_label.hide()
        self.delete_button.hide()
        self.slider.hide()
        self.min_label.hide()
        self.max_label.hide()
        self.widget_visible = 0

    def show_slider_box(self):
        self.name_label.show()
        self.result_label.show()
        self.delete_button.show()
        self.slider.show()
        self.min_label.show()
        self.max_label.show()

        self.first_row.addWidget(self.name_label, alignment=Qt.AlignmentFlag.AlignLeft)
        self.first_row.addWidget(
            self.result_label, alignment=Qt.AlignmentFlag.AlignHCenter
        )
        self.first_row.addWidget(
            self.delete_button, alignment=Qt.AlignmentFlag.AlignRight
        )

        self.second_row.addWidget(self.min_label)
        self.second_row.addWidget(self.slider)
        self.second_row.addWidget(self.max_label)

        self.first_row.setAlignment(Qt.AlignmentFlag.AlignBottom)
        self.second_row.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.widget_visible = 1

    def __result_display(self):
        return f"Current value: {self.slider.rpc_value}"


class RPCLabel(QLabel):
    def __init__(self, name, parent=None):
        QLabel.__init__(self, name, parent)
        self.setFont(qfont())


class RPCButton(QPushButton):
    def __init__(self, parent=None):
        QPushButton.__init__(self, parent)
        self.setIcon(QIcon(str(Path(__file__).resolve().parent / "./delete.xpm")))
        self.setIconSize(QSize(35, 25))
        self.setStyleSheet(generate_qss())


class EditBox(QLineEdit):
    def __init__(self, default: str, parent=None):
        QLineEdit.__init__(self, parent)
        self.setText(default)
        self.setFont(qfont())
        self.setFixedWidth(
            max(50, min(self.fontMetrics().horizontalAdvance(self.text()) + 10, 90))
        )
        self.textChanged.connect(
            lambda: self.setFixedWidth(
                max(50, min(self.fontMetrics().horizontalAdvance(self.text()) + 10, 90))
            )
        )
        self.setValidator(QDoubleValidator())
        self.setFocusPolicy(Qt.FocusPolicy.ClickFocus)
        self.setStyleSheet(generate_qss())
        self.returnPressed.connect(lambda: self.clearFocus())


class RPCSlider(QSlider):
    def __init__(
        self, rpc: RPC, min_val: int | float, max_val: int | float, parent=None
    ):
        self.rpc = rpc
        self.int_scale = 100 if rpc.arg_type == float else 1
        self.rpc_value = self.rpc.call()
        self.value_scaled = self.scale(self.rpc_value)
        self.updating = False

        QSlider.__init__(self, parent)
        self.setOrientation(Qt.Orientation.Horizontal)
        self.setRange(self.scale(min_val), self.scale(max_val))
        self.setValue(self.value_scaled)
        self.setSingleStep(1)
        self.setPageStep(10)
        self.setStyleSheet(generate_qss())
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.valueChanged.connect(self.update_slider)
        self.sliderPressed.connect(lambda: self.setFocus())

    def update_slider(self, value: int | str):
        if not self.updating:  # don't recursively call this
            self.updating = True
            value_real = self.descale(value)
            value = self.rpc.call(value_real)

            if type(value) is str:
                if value.startswith(RPC_ERROR()):
                    self.setValue(self.value_scaled)
                    self.rpc_value = "ERROR"
                elif value == PROXY_FATAL:
                    self.setValue(self.value_scaled)
                    self.rpc_value = "FATAL"
            else:
                self.rpc_value = value
                self.value_scaled = self.scale(self.rpc_value)
                self.setValue(self.value_scaled)

            self.updating = False

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Right or event.key() == Qt.Key.Key_Left:
            slider_width = self.width() * self.devicePixelRatioF()
            step_size = (self.maximum() - self.minimum()) // slider_width + 1
            step_value = self.call() + (
                step_size if event.key() == Qt.Key.Key_Right else -step_size
            )
            self.update_slider(step_value)
        elif event.key() == Qt.Key.Key_Escape or event.text().isalpha():
            self.clearFocus()

    def scale(self, val: int | float | str) -> int:
        return min(round(self.rpc.to_arg_type(val) * self.int_scale), 2**31 - 1)

    def descale(self, val: int) -> int | float:
        return self.rpc.to_arg_type(val / self.int_scale)
