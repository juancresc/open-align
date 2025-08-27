# open-align

open-align is a Python CLI tool to align and crop a set of handheld photos.
It detects ORB features, estimates similarity transforms, warps all images 
into the reference frame (the first image), and computes the common overlap crop
so black borders from alignment are removed.

# -------------------------------------------------------------------
# Installation
# -------------------------------------------------------------------

# Clone and install in editable mode:

git clone https://github.com/yourname/open-align.git
cd open-align
python -m venv .venv
source .venv/bin/activate
pip install -e .

# Requires Python ≥ 3.9. Dependencies:
# - opencv-python
# - numpy
# - typer
# - rich

# -------------------------------------------------------------------
# Usage
# -------------------------------------------------------------------

# Run via the module entrypoint:

python -m open_align align [OPTIONS] FILES...

# -------------------------------------------------------------------
# Example
# -------------------------------------------------------------------

python -m open_align align \
  /Users/juan/Pictures/cam/aug-25/movimiento/IMG_0801.jpg \
  /Users/juan/Pictures/cam/aug-25/movimiento/IMG_0803.jpg \
  /Users/juan/Pictures/cam/aug-25/movimiento/IMG_0804.jpg \
  /Users/juan/Pictures/cam/aug-25/movimiento/IMG_0805.jpg \
  /Users/juan/Pictures/cam/aug-25/movimiento/IMG_0806.jpg \
  /Users/juan/Pictures/cam/aug-25/movimiento/IMG_0807.jpg \
  /Users/juan/Pictures/cam/aug-25/movimiento/IMG_0808.jpg \
  /Users/juan/Pictures/cam/aug-25/movimiento/IMG_0809.jpg \
  --erode 200

# This will:
# 1. Detect ORB features (default --nfeatures 4000).
# 2. Estimate transforms for each image → reference.
# 3. Warp images into reference coordinates.
# 4. Compute overlap across masks, eroded by 200px for safety.
# 5. Save aligned + cropped results as aligned_cropped_###.jpg in the working directory.

# -------------------------------------------------------------------
# Options
# -------------------------------------------------------------------

# -n, --nfeatures INTEGER   Number of ORB features to detect (default: 4000)
# -e, --erode INTEGER       Erosion size for overlap mask (default: 4)
# -v, --version             Show version and exit

# -------------------------------------------------------------------
# Output
# -------------------------------------------------------------------

# - ref_matches_all.png  → keypoints detected on the reference image.
# - aligned_###.png      → warped images (optional, for debugging).
# - aligned_cropped_###.jpg → final aligned + cropped images.

# -------------------------------------------------------------------
# License
# -------------------------------------------------------------------

# MIT © 2025
