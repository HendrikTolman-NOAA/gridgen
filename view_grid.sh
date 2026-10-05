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
# @date Update: 2026-10-05
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
import os
import sys
from pathlib import Path
from PIL import Image
import matplotlib
import matplotlib.pyplot as plt

img_path = "${IMAGE_FILE}"
print(f"Loading '{img_path}'...")

display_env = os.environ.get("DISPLAY")
wayland_env = os.environ.get("WAYLAND_DISPLAY")

if not display_env and not wayland_env:
    print("WARNING: Neither DISPLAY nor WAYLAND_DISPLAY environment variable is set.")
    print("No active graphical display server detected in current environment.")
    print("Matplotlib is running in non-interactive backend mode ('agg'), so no window will appear on screen.")
    print("")
    print("Troubleshooting steps to display graphics on screen:")
    print("  1. Ensure you are running in a graphical desktop or GUI environment.")
    print("  2. If connected remotely via SSH, enable X11 forwarding:")
    print("       ssh -X user@hostname   or   ssh -Y user@hostname")
    print("  3. Ensure the DISPLAY environment variable is set (e.g., export DISPLAY=:0).")

try:
    img = Image.open(img_path)
    print(f"Image Format: {img.format}, Size: {img.size[0]}x{img.size[1]} pixels, Mode: {img.mode}")

    backend = matplotlib.get_backend().lower()
    print(f"Matplotlib backend: {matplotlib.get_backend()}")

    if backend in ["agg", "pdf", "ps", "svg", "cairo"] or not (display_env or wayland_env):
        print("Skipping GUI figure window display because Matplotlib backend is non-interactive or no display server is connected.")
    else:
        # Display image in window
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.imshow(img)
        ax.set_title(f"WAVEWATCH Grid Graphics: {Path(img_path).name}", fontsize=12, fontweight="bold")
        ax.axis("off")
        plt.tight_layout()
        plt.show()
except Exception as e:
    print(f"Error displaying window: {e}")
    print("Display window could not be opened. Please verify your X11/Wayland display configuration.")
EOF

echo "Display task finished for ${IMAGE_FILE}."
