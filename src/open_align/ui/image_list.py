from __future__ import annotations
from pathlib import Path
from typing import Iterable, List

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon, QPixmap, QImageReader
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QIcon, QPixmap, QImageReader, QAction

from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QListWidget,
    QListWidgetItem,
    QFileDialog,
    QPushButton,
    QLabel,
    QStyle,
    QMessageBox,
    QSplitter,
    QSizePolicy,
    QDialog,
    QTabWidget,
)

from . import THUMB_SIZE, SUPPORTED_SUFFIXES

def _read_thumb(path: Path):
    reader = QImageReader(str(path))
    if not reader.canRead():
        return None
    size = reader.size()
    if size.isValid():
        w, h = size.width(), size.height()
        if w > h:
            scaled_w = THUMB_SIZE.width()
            scaled_h = max(1, h * scaled_w // max(1, w))
        else:
            scaled_h = THUMB_SIZE.height()
            scaled_w = max(1, w * scaled_h // max(1, h))
        reader.setScaledSize(reader.size().scaled(scaled_w, scaled_h, Qt.AspectRatioMode.KeepAspectRatio))
    img = reader.read()
    if img.isNull():
        return None
    return QPixmap.fromImage(img)

class PreviewDialog(QDialog):
    """Simple zoom-to-fit preview; resizes with the dialog."""
    def __init__(self, path: Path, parent: QWidget | None = None):
        super().__init__(parent)
        self.setWindowTitle(path.name)
        self.resize(900, 700)
        self._pix = QPixmap(str(path))

        self.label = QLabel("Unable to load image." if self._pix.isNull() else "")
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout = QVBoxLayout(self)
        layout.addWidget(self.label)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if not self._pix.isNull():
            self.label.setPixmap(
                self._pix.scaled(
                    self.size() - QSize(40, 40),
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
            )
class ImageList(QListWidget):
    """Icon-mode list that accepts external drops of image files."""
    def __init__(self, preview_label: QLabel | None = None, parent: QWidget | None = None):
        super().__init__(parent)
        self.preview_label = preview_label
        self.setViewMode(QListWidget.ViewMode.IconMode)
        self.setIconSize(THUMB_SIZE)
        self.setResizeMode(QListWidget.ResizeMode.Adjust)
        self.setMovement(QListWidget.Movement.Static)
        self.setSpacing(8)
        self.setUniformItemSizes(False)
        self.setWordWrap(True)
        self.setSelectionMode(QListWidget.SelectionMode.ExtendedSelection)

        # Accept external file drops, but don't allow reordering
        self.setAcceptDrops(True)
        self.setDragDropMode(QListWidget.DragDropMode.NoDragDrop)

        # Quick tips
        self.setToolTip("Drop images here • Double-click a thumbnail to preview")

        self.itemDoubleClicked.connect(self._open_preview)

    # ---- Drag & Drop handlers ----
    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event):
        urls = event.mimeData().urls()
        paths = [Path(u.toLocalFile()) for u in urls if u.isLocalFile()]
        self.add_images(paths)
        event.acceptProposedAction()

    # ---- Public API ----
    def add_images(self, paths: Iterable[Path]):
        added = 0
        for p in paths:
            if p.is_dir():
                # Add images from directory (non-recursive)
                files = [f for f in p.iterdir() if f.suffix.lower() in SUPPORTED_SUFFIXES]
                added += self._add_many(files)
            else:
                if p.suffix.lower() in SUPPORTED_SUFFIXES:
                    added += self._add_one(p)
        if added == 0:
            QMessageBox.information(self, "No images", "No supported image files were added.")

    def remove_selected(self):
        for item in list(self.selectedItems()):
            row = self.row(item)
            self.takeItem(row)

    def clear_all(self):
        self.clear()
        if self.preview_label is not None:
            self.preview_label.clear()
            self.preview_label.setText("Drop images →")

    # ---- Internals ----
    def _add_many(self, files: List[Path]) -> int:
        count = 0
        for f in files:
            count += self._add_one(f)
        return count

    def _add_one(self, path: Path) -> int:
        # Avoid duplicates: compare stored path in UserRole
        for i in range(self.count()):
            if self.item(i).data(Qt.ItemDataRole.UserRole) == str(path):
                return 0

        pix = _read_thumb(path)
        if pix is None:
            return 0

        item = QListWidgetItem(QIcon(pix), path.name)
        item.setSizeHint(QSize(THUMB_SIZE.width() + 16, THUMB_SIZE.height() + 28))
        item.setData(Qt.ItemDataRole.UserRole, str(path))
        item.setToolTip(str(path))
        self.addItem(item)
        return 1

    def _open_preview(self, item: QListWidgetItem):
        path = Path(item.data(Qt.ItemDataRole.UserRole))
        dlg = PreviewDialog(path, parent=self)
        dlg.exec()

        # Also reflect the preview in the side pane if present
        if self.preview_label is not None and path.exists():
            pix = QPixmap(str(path))
            if not pix.isNull():
                scaled = pix.scaled(
                    self.preview_label.size(),
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
                self.preview_label.setPixmap(scaled)

