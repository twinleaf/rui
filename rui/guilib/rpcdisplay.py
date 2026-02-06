from rui.lib.rpc import RPC
from PyQt6.QtWidgets import QPushButton, QSlider, QLabel, QLineEdit, QVBoxLayout, QHBoxLayout
from PyQt6.QtGui import QDoubleValidator, QIcon
from PyQt6.QtCore import Qt
from rui.guilib.style import qfont, generate_qss

class RPCDisplay:
    def __init__(self, rpc: RPC, min_val: int | float, max_val: int | float):
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

        self.grid_layout = QVBoxLayout()
        self.first_row = QHBoxLayout()
        self.second_row = QHBoxLayout()
        self.second_row.setSpacing(8)
        self.first_row.addWidget(self.name_label)
        self.first_row.addWidget(self.result_label, alignment = Qt.AlignmentFlag.AlignHCenter)
        self.first_row.addWidget(self.delete_button, alignment = Qt.AlignmentFlag.AlignRight)
        self.second_row.addWidget(self.min_label)
        self.second_row.addWidget(self.slider)
        self.second_row.addWidget(self.max_label)
        self.grid_layout.addLayout(self.first_row)
        self.grid_layout.addLayout(self.second_row)


    def make_label(self, name) -> QLabel:
        label = QLabel(name)
        label.setFont(qfont())
        return label

    def make_edit(self, default: str, edit_func: callable) -> QLineEdit:
        edit = QLineEdit()
        edit.setText(default)
        edit.setFont(qfont())
        edit.setFixedWidth(50)
        edit.setValidator(QDoubleValidator())
        edit.setFocusPolicy(Qt.FocusPolicy.ClickFocus)
        edit.setStyleSheet(generate_qss())
        edit.returnPressed.connect(lambda: edit_func(self.__scale(edit.text())))
        return edit

    def make_slider(self, min_val: int | float, max_val: int | float) -> QSlider:
        self.updating = False
        slider = QSlider(Qt.Orientation.Horizontal)
        slider.setRange(self.__scale(min_val), self.__scale(max_val))
        slider.setValue(self.value_scaled)
        slider.setSingleStep(1)
        slider.setPageStep(10)
        slider.setStyleSheet(generate_qss())
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
        icon = QIcon().fromTheme("document-new")
        button.setIcon(icon)
        button.setStyleSheet(generate_qss())
        if (self.widget_visible == True):
            button.clicked.connect(self.hide_slider_box)
        return button

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
        self.widget_visible = False
    
    def show_slider_box(self):
        self.name_label.show()
        self.result_label.show()
        self.delete_button.show()
        self.slider.show()
        self.min_label.show()
        self.max_label.show() 
        self.first_row.addWidget(self.name_label, alignment = Qt.AlignmentFlag.AlignLeft)
        self.first_row.addWidget(self.result_label, alignment = Qt.AlignmentFlag.AlignHCenter)
        self.first_row.addWidget(self.delete_button, alignment = Qt.AlignmentFlag.AlignRight)
        self.second_row.addWidget(self.min_label)
        self.second_row.addWidget(self.slider)
        self.second_row.addWidget(self.max_label)
        #TODO: Determine why these are snapping to the bottom, potentially something to do with the 
        #rpc vbox total layout, could also be the initial creation of the rpc displays causing this issue. 
        #could create separate rpc display function in main app and determine
        #Could also be a glitch because it's running when connected 
        self.first_row.setAlignment(Qt.AlignmentFlag.AlignBottom)
        self.second_row.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.widget_visible = True

    def __get_value(self):
        self.value = self.rpc.value()
        self.value_scaled = self.__scale(self.value)
    def __result_display(self): 
        return f"Current value: {self.value}"
    def __scale(self, val: int | float ) -> int: 
        return round(self.rpc.arg_type(val) * self.scale)
    def __descale(self, val: int) -> int | float: 
        return self.rpc.arg_type(val / self.scale)
