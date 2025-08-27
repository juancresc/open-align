from __future__ import annotations
import sys
from PyQt6.QtWidgets import QApplication
from .ui.main_window import MainWindow

def launch_gui():
    app = QApplication.instance() or QApplication(sys.argv)
    win = MainWindow()
    win.show()
    app.exec()

