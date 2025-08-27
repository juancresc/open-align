# Open Align

A Python tool for aligning and cropping handheld photos using computer vision techniques. Open Align detects ORB features, estimates similarity transforms, warps images into a reference frame, and computes the common overlap crop to remove black borders from alignment.

## Features

- **Feature Detection**: Uses ORB (Oriented FAST and Rotated BRIEF) features for robust image matching
- **Image Alignment**: Automatically aligns multiple handheld photos to a reference image
- **Smart Cropping**: Removes black borders and computes optimal crop regions
- **GUI Interface**: Modern PyQt6-based graphical interface for easy image selection and preview
- **CLI Support**: Command-line interface for batch processing and automation
- **Cross-platform**: Works on Windows, macOS, and Linux

## Installation

### Prerequisites

- Python ≥ 3.9
- Git

### Install from Source

```bash
# Clone the repository
git clone https://github.com/yourname/open-align.git
cd open-align

# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install in editable mode
pip install -e .
```

### Dependencies

The following packages are automatically installed:
- `opencv-python` - Computer vision and image processing
- `numpy` - Numerical computing
- `typer` - CLI framework
- `rich` - Terminal formatting


## Usage

#### Example

```bash
python -m open_align align \
  /path/to/image1.jpg \
  /path/to/image2.jpg \
  /path/to/image3.jpg \
  --nfeatures 4000 \
  --erode 200
```

## Options

| Option | Description | Default |
|--------|-------------|---------|
| `-n, --nfeatures INTEGER` | Number of ORB features to detect | 4000 |
| `-e, --erode INTEGER` | Erosion size for overlap mask (pixels) | 4 |
| `-v, --version` | Show version and exit | - |

## How It Works

1. **Feature Detection**: Detects ORB features in all input images
2. **Feature Matching**: Matches features between each image and the reference
3. **Transform Estimation**: Estimates similarity transforms for alignment
4. **Image Warping**: Warps all images into the reference coordinate system
5. **Overlap Computation**: Finds the common overlap region across all images
6. **Cropping**: Applies erosion and crops to remove black borders
7. **Output**: Saves aligned and cropped images

## Output Files

- `ref_matches_all.png` - Keypoints detected on the reference image (for debugging)
- `aligned_###.png` - Warped images before cropping (optional, for debugging)
- `aligned_cropped_###.jpg` - Final aligned and cropped images

## Example Workflow

```bash
# 1. Select images in the GUI or specify them on command line
python -m open_align align image1.jpg image2.jpg image3.jpg

# 2. The tool will:
#    - Detect 4000 ORB features per image
#    - Align all images to the first image (reference)
#    - Compute the common overlap region
#    - Crop to remove black borders
#    - Save results as aligned_cropped_001.jpg, aligned_cropped_002.jpg, etc.
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

MIT © 2025
