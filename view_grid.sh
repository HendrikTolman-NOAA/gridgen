#!/usr/bin/env bash
# WAVEWATCH III (WW3) / WAVEWATCH IV (WW4) Gridgen Package
#
# Copyright 2026 National Weather Service (NWS), NOAA. All rights reserved.
# NWS often uses Generative AI (GenAI) for code development and refactoring.
# Whenever GenAI is used, NWS requires a full human review of code before it
# is added to its repositories.
#
# @author Aldgisl (Agentic AI), Jules (Agentic AI), Hendrik Tolman
# @date Initial: 2026-10-05
#
# Utility script to display generated grid plot graphics in the present window.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export PYTHONPATH="${SCRIPT_DIR}:${PYTHONPATH:-}"

IMAGE_FILE=""

usage() {
  cat << 'EOF'
Usage: ./view_grid.sh [IMAGE_FILE]

Utility script to display generated WAVEWATCH III / IV grid plot graphics in the present window.

Options:
  IMAGE_FILE             Path to image file (default: searches for ww4_grid.jpg, ww4_grid.png, ww4_grid.gif, etc.)
  -h, --help             Display this help message and exit

Description:
  This script opens and displays the generated grid plot image (JPG, PNG, GIF, PDF)
  in a GUI image window or interactive viewer.
EOF
}

# Parse Arguments
while [[ $# -gt 0 ]]; do
  case "$1" in
    -h|--help)
      usage
      exit 0
      ;;
    *)
      if [ -z "$IMAGE_FILE" ]; then
        IMAGE_FILE="$1"
        shift 1
      else
        echo "Error: Unknown argument: $1" >&2
        usage
        exit 1
      fi
      ;;
  esac
done

# If no image file provided, search for default generated image files
if [ -z "$IMAGE_FILE" ]; then
  for candidate in "ww4_grid.jpg" "ww4_grid.png" "ww4_grid.gif" "ww4_grid_display.jpg" "ww4_grid_display.gif" "ww4_grid_display.png"; do
    if [ -f "$candidate" ]; then
      IMAGE_FILE="$candidate"
      break
    fi
  done
fi

if [ -z "$IMAGE_FILE" ] || [ ! -f "$IMAGE_FILE" ]; then
  echo "Error: Grid graphics image file not found." >&2
  echo "Please generate plot graphics first using './plot_grid.sh' or specify an image file path." >&2
  exit 1
fi

echo "========================================================================"
echo " Displaying WAVEWATCH Grid Graphics: ${IMAGE_FILE}"
echo "========================================================================"

# Display using Python Matplotlib/PIL viewer in present window
python3 - << EOF
import sys
from pathlib import Path
from PIL import Image
import matplotlib.pyplot as plt
import matplotlib.image as mpimg

img_path = "${IMAGE_FILE}"
print(f"Loading '{img_path}'...")

try:
    img = Image.open(img_path)
    print(f"Image Format: {img.format}, Size: {img.size[0]}x{img.size[1]} pixels, Mode: {img.mode}")

    # Display image in window
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.imshow(img)
    ax.set_title(f"WAVEWATCH Grid Graphics: {Path(img_path).name}", fontsize=12, fontweight="bold")
    ax.axis("off")
    plt.tight_layout()
    plt.show()
except Exception as e:
    print(f"Display window info: {e}")
EOF

echo "Display completed for ${IMAGE_FILE}."
