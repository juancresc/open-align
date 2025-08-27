from __future__ import annotations
from PyQt6.QtCore import QSize

THUMB_SIZE = QSize(200, 200)
SUPPORTED_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".gif", ".tif", ".tiff", ".heic"}

# Where the feature image will be loaded from on step 2
FEATURE_IMAGE_PATH = "tmp/features.png"
