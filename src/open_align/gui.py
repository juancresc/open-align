from __future__ import annotations

import sys
from pathlib import Path
from typing import Iterable, List

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
)


THUMB_SIZE = QSize(200, 200)
SUPPORTED_SUFFIXES = {
    ".png", ".jpg", ".jpeg", ".webp", ".bmp", ".gif", ".tif", ".tiff", ".heic"
}


def _read_thumb(path: Path, max_size: QSize = THUMB_SIZE) -> QPixmap | None:
    """Memory-friendly thumbnail loader using QImageReader scaling."""
    reader = QImageReader(str(path))
    if not reader.canRead():
        return None

    # Preserve aspect ratio; scale so the longest edge == max_size edge
    size = reader.size()
    if size.isValid():
        w, h = size.width(), size.height()
        if w > h:
            scaled = QSize(max_size.width(), max(1, h * max_size.width() // max(1, w)))
        else:
            scaled = QSize(max(1, w * max_size.height() // max(1, h)), max_size.height())
        reader.setScaledSize(scaled)

    img = reader.read()
    if img.isNull():
        return None
    return QPixmap.fromImage(img)


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


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("open-align — Image DnD Gallery")
        self.resize(1100, 720)

        # Menu (macOS-friendly)
        file_menu = self.menuBar().addMenu("&File")
        act_open = QAction(self.style().standardIcon(QStyle.StandardPixmap.SP_DialogOpenButton), "Add Images…", self)
        act_open.triggered.connect(self._pick_files)
        file_menu.addAction(act_open)

        act_clear = QAction("Clear All", self)
        act_clear.triggered.connect(self._clear_all)
        file_menu.addAction(act_clear)

        file_menu.addSeparator()
        act_quit = QAction("Quit", self)
        act_quit.triggered.connect(self.close)
        file_menu.addAction(act_quit)

        # Toolbar buttons
        bar = self.addToolBar("Main")
        bar.setMovable(False)
        bar.addAction(act_open)
        bar.addAction(act_clear)

        # Central layout: gallery (left) + live preview (right)
        central = QWidget(self)
        self.setCentralWidget(central)

        outer = QVBoxLayout(central)
        splitter = QSplitter(Qt.Orientation.Horizontal, central)
        outer.addWidget(splitter)

        # Right-side large preview
        self.preview = QLabel("Drop images →")
        self.preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        # Left gallery list (drag & drop target)
        self.gallery = ImageList(preview_label=self.preview)
        splitter.addWidget(self.gallery)
        splitter.addWidget(self.preview)
        splitter.setSizes([700, 400])

        # Bottom action row
        buttons = QHBoxLayout()
        btn_add = QPushButton("Add Images…")
        btn_add.clicked.connect(self._pick_files)
        btn_remove = QPushButton("Remove Selected")
        btn_remove.clicked.connect(self.gallery.remove_selected)
        btn_clear = QPushButton("Clear All")
        btn_clear.clicked.connect(self.gallery.clear_all)
        buttons.addWidget(btn_add)
        buttons.addStretch(1)
        buttons.addWidget(btn_remove)
        buttons.addWidget(btn_clear)
        outer.addLayout(buttons)

        # Selection updates preview
        self.gallery.itemSelectionChanged.connect(self._selection_changed)

        # Accept drops on the whole window (forward to gallery)
        self.setAcceptDrops(True)

    # Window-level drop handling -> forward to gallery
    def dragEnterEvent(self, e):
        if e.mimeData().hasUrls():
            e.acceptProposedAction()
        else:
            e.ignore()

    def dragMoveEvent(self, e):
        if e.mimeData().hasUrls():
            e.acceptProposedAction()
        else:
            e.ignore()

    def dropEvent(self, e):
        urls = e.mimeData().urls()
        paths = [Path(u.toLocalFile()) for u in urls if u.isLocalFile()]
        self.gallery.add_images(paths)
        e.acceptProposedAction()

    # Helpers
    def _pick_files(self):
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Select Images",
            str(Path.home()),
            "Images (*.png *.jpg *.jpeg *.webp *.bmp *.gif *.tif *.tiff *.heic);;All Files (*)",
        )
        self.gallery.add_images(Path(f) for f in files)

    def _clear_all(self):
        self.gallery.clear_all()

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
                pix.scaled(
                    self.preview.size(),
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
            )

def launch_gui():
    app = QApplication.instance() or QApplication(sys.argv)
    win = MainWindow()
    win.show()
    app.exec()
