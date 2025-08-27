from __future__ import annotations
from pathlib import Path
from typing import Optional

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QSizePolicy

from .. import FEATURE_IMAGE_PATH

class CroppingTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._pix: Optional[QPixmap] = None

        outer = QVBoxLayout(self)
        self.label = QLabel("Cropping preview will appear here.")
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        hint = QLabel(f"This tab loads: {FEATURE_IMAGE_PATH}")
        hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hint.setStyleSheet("color: #666;")

        outer.addWidget(self.label)
        outer.addWidget(hint)

    def load_feature_image(self, path: Path | None = None) -> bool:
        path = Path(path or FEATURE_IMAGE_PATH)
        if not path.exists():
            self._pix = None
            self.label.setText(f"Missing: {path}")
            self.label.setPixmap(QPixmap())
            return False
        pix = QPixmap(str(path))
        if pix.isNull():
            self._pix = None
            self.label.setText(f"Unreadable: {path}")
            self.label.setPixmap(QPixmap())
            return False
        self._pix = pix
        self._rescale()
        self.label.setText("")
        return True

    def resizeEvent(self, e):
        super().resizeEvent(e)
        self._rescale()

    def _rescale(self):
        if isinstance(self._pix, QPixmap) and not self._pix.isNull():
            self.label.setPixmap(
                self._pix.scaled(self.label.size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            )
