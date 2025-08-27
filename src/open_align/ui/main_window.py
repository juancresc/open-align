from __future__ import annotations
from PyQt6.QtWidgets import QMainWindow, QTabWidget
from PyQt6.QtGui import QAction
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import Qt

from .tabs.images_selector_tab import ImagesSelectorTab
from .tabs.cropping_tab import CroppingTab

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("open-align")
        self.resize(1100, 720)

        # Menu
        file_menu = self.menuBar().addMenu("&File")
        act_quit = QAction("Quit", self); act_quit.triggered.connect(self.close)
        file_menu.addAction(act_quit)

        # Tabs
        self.tabs = QTabWidget(self)
        self.setCentralWidget(self.tabs)

        self.tab_images = ImagesSelectorTab(self)
        self.tab_features = CroppingTab(self)

        self.tabs.addTab(self.tab_images, "Images selector")
        self.tabs.addTab(self.tab_features, "Cropping")

        # Wire: proceed button switches to features tab and loads tmp/features.png
        self.tab_images.proceed.connect(self._go_to_features)

    def _go_to_features(self):
        self.tab_features.load_feature_image()  # loads FEATURE_IMAGE_PATH
        self.tabs.setCurrentWidget(self.tab_features)
