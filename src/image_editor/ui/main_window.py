import sys

from PySide6.QtCore import QSize, Qt
from PySide6.QtWidgets import QMainWindow, QMenu
from PySide6.QtGui import QAction 
from .menu_bar import MainMenu, MENU_SPEC, MENU_STYLESHEET


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("PEdit")
        self.resize(1000,800)

        menu_bar, register = MainMenu.create_menu(self, MENU_SPEC, stylesheet=MENU_STYLESHEET)
