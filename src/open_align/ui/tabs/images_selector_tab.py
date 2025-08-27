from __future__ import annotations
from pathlib import Path
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QSplitter, QLabel, QPushButton, QFileDialog, QSizePolicy

from ..image_list import ImageList
from typing import Iterable
from PyQt6.QtWidgets import QLabel
from PyQt6.QtCore import Qt
from pathlib import Path

class ForwardDropLabel(QLabel):
    """A QLabel that accepts file drops and forwards them via a callback."""
    def __init__(self, on_paths: callable, parent=None):
        super().__init__(parent)
        self._on_paths = on_paths
        self.setAcceptDrops(True)

    def dragEnterEvent(self, e):
        e.acceptProposedAction() if e.mimeData().hasUrls() else e.ignore()

    def dragMoveEvent(self, e):
        e.acceptProposedAction() if e.mimeData().hasUrls() else e.ignore()

    def dropEvent(self, e):
        urls = e.mimeData().urls()
        paths = [Path(u.toLocalFile()) for u in urls if u.isLocalFile()]
        if paths:
            self._on_paths(paths)
        e.acceptProposedAction()


class ImagesSelectorTab(QWidget):
    proceed = pyqtSignal()  # emitted when user clicks "Go to Feature Detection"

    def __init__(self, parent=None):
        super().__init__(parent)

        outer = QVBoxLayout(self)
        splitter = QSplitter(Qt.Orientation.Horizontal, self)
        outer.addWidget(splitter)
        
        # 1) Create the drop-enabled preview first
        self.preview = ForwardDropLabel(on_paths=self.gallery.add_images if hasattr(self, "gallery") else lambda _: None)
        self.preview.setText("Drop images →")
        self.preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        # 2) Now create the gallery, injecting the already-created preview
        self.gallery = ImageList(preview_label=self.preview, parent=self)

        # 3) Add both to the splitter
        splitter.addWidget(self.gallery)
        splitter.addWidget(self.preview)
        splitter.setSizes([700, 400])

        # buttons
        row = QHBoxLayout()
        btn_add = QPushButton("Add Images…"); btn_add.clicked.connect(self._pick_files)
        btn_remove = QPushButton("Remove Selected"); btn_remove.clicked.connect(self.gallery.remove_selected)
        btn_clear = QPushButton("Clear All"); btn_clear.clicked.connect(self.gallery.clear_all)
        btn_next = QPushButton("Go to cropping →"); btn_next.setDefault(True); btn_next.clicked.connect(self._on_next)

        row.addWidget(btn_add); row.addStretch(1); row.addWidget(btn_remove); row.addWidget(btn_clear); row.addWidget(btn_next)
        outer.addLayout(row)

        self.gallery.itemSelectionChanged.connect(self._selection_changed)

        self.setAcceptDrops(True)

    def dragEnterEvent(self, e):
        e.acceptProposedAction() if e.mimeData().hasUrls() else e.ignore()

    def dragMoveEvent(self, e):
        e.acceptProposedAction() if e.mimeData().hasUrls() else e.ignore()

    def dropEvent(self, e):
        urls = e.mimeData().urls()
        paths = [Path(u.toLocalFile()) for u in urls if u.isLocalFile()]
        if paths:
            self.gallery.add_images(paths)
        e.acceptProposedAction()

    def _pick_files(self):
        files, _ = QFileDialog.getOpenFileNames(
            self, "Select Images", str(Path.home()),
            "Images (*.png *.jpg *.jpeg *.webp *.bmp *.gif *.tif *.tiff *.heic);;All Files (*)",
        )
        self.gallery.add_images(Path(f) for f in files)

    def _selection_changed(self):
        items = self.gallery.selectedItems()
        if not items:
            self.preview.setText("Drop images →")
            self.preview.setPixmap(QPixmap())
            return
        path = Path(items[0].data(Qt.ItemDataRole.UserRole))
        pix = QPixmap(str(path))
        if not pix.isNull():
            self.preview.setPixmap(
                pix.scaled(self.preview.size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            )

    def _on_next(self):
        self.proceed.emit()
