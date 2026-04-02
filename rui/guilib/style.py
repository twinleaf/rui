import random

from PyQt6.QtGui import QFont


def qfont(size: int = 14):
    return QFont("Ubuntu", size)


def generate_qss() -> str:
    return f"""
    QComboBox {{
        border: 2px solid grey;
        border-radius: 5px;
        min-width: 6em;
        color:black;
        background-color:white;
    }}

    QComboBox:hover{{background-color:lightgrey}}

    QComboBox QAbstractItemView {{
        border-color:2px solid black;
        border-radius: 5px;
        color:white;
        selection-background-color:lightgrey
    }}

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

    QSlider:focus {{
        border: 2px solid lightblue;
        border-radius: 5px;
    }}

    QSlider::sub-page:horizontal {{
        background: {_random_hex(500)}; /* color for the part before the handle */
    }}

    QLineEdit {{
        border: 1px solid #5c5c5c;
        border-radius: 9px;
    }}

    QLineEdit::focus{{
        border: 2px solid blue;
    }}

    QPushButton {{
        background-color: white;
        border-color: black;
        border: 1px solid;
        border-radius: 5px;
    }}
    """


def _random_hex(total: int) -> str:
    ret = "#"
    for i in range(3):
        max = 255 if total > 255 else total
        r = random.randint(0, max)
        ret += hex(r)[2:].zfill(2)
    return ret
