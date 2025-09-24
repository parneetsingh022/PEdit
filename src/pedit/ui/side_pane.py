
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel,
    QSizePolicy
)

from pedit.core.theme import color_theme

class SidePane(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()
        label = QLabel("HELLO this is side pane")
        layout.setContentsMargins(0,0,0,0)
        layout.addWidget(label, alignment=Qt.AlignTop)
        layout.addStretch(1)
        self.setLayout(layout) 

        self.setStyleSheet(
            f"background-color: {color_theme.COLOR_BACKGROUND};"
            "color:black;"
            f"border-right: 2px solid {color_theme.COLOR_BORDER};"
        )
        # Ensure the widget actually paints its stylesheet background
        self.setAttribute(Qt.WA_StyledBackground, True)
        # Allow it to grow; ensure no unintended minimum height
        self.setMinimumHeight(0)
        self.setFixedWidth(300)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)

