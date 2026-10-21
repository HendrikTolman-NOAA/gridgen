#!/usr/bin/env bash
# WAVEWATCH III (WW3) / WAVEWATCH IV (WW4) Gridgen Package
#
# Copyright 2026 National Weather Service (NWS), NOAA. All rights reserved.
# NWS often uses Generative AI (GenAI) for code development and refactoring.
# Whenever GenAI is used, NWS requires a full human review of code before it
# is added to its repositories.
#
# @author Aldgisl (Agentic AI), Hendrik Tolman
# @author Jules (Agentic AI) (contributor)
# @date Initial: 2026-10-05
# @date Latest Update: 2026-10-21
#
# Shell driver script to generate graphical grid bathymetry plots.

set -euo pipefail

ORIG_DIR="$(pwd)"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"
export PYTHONPATH="${SCRIPT_DIR}:${PYTHONPATH:-}"

INPUT_FILE="ww4_grid_ugrid.nc"
OUTPUT_FILE=""
FORMAT="jpg"
TITLE="WAVEWATCH IV Grid"
SUBTITLE="Bathymetry and Orography"
NO_TITLE=0
NO_SUBTITLE=0
MASK_FLAG=""
MAX_DEPTH="-500"
MAX_OROGRAPHY="10"
DISPLAY_FLAG="--no-display"
ZOOM_ARGS=()

INPUT_FILE_SPECIFIED=0
OUTPUT_FILE_SPECIFIED=0

usage() {
  cat << 'EOF'
Usage: ./plot_grid.sh [OPTIONS]

Utility script to graphically display resulting WAVEWATCH III / IV grids.

Options:
  -i, --input PATH       Input dataset file path (_ugrid.nc, _coards.nc, or ASCII prefix) (default: ww4_grid_ugrid.nc)
  -o, --output PATH      Output plot image file path (default: <GRIDNAME>.<format>)
  -f, --format FORMAT    Output graphic format: jpg, png, pdf, eps, or gif (default: jpg)
  --title TITLE          Custom main figure title (default: WAVEWATCH IV Grid)
  --no-title             Disable main figure title
  --subtitle SUBTITLE    Custom figure subtitle (default: Bathymetry and Orography)
  --no-subtitle          Disable figure subtitle
  --no-mask              Disable land-sea mask
  --zoom LON LAT FACTOR  Zoom view centered at central longitude and latitude with zoom factor
  --max-depth DEPTH      Maximum depth limit for color scale (default: -500)
  --max-orography OROG   Maximum orography limit for color scale in meters (default: 10)
  --display              Display figure window interactively
  --no-display           Disable interactive figure window display
  -h, --help             Display this help message and exit

Description:
  This script executes the Python grid visualization module (`gridgen.vis`)
  to produce bathymetry depth plots in JPG, PNG, PDF, EPS, or GIF formats.
EOF
}

# Parse Arguments
while [[ $# -gt 0 ]]; do
  case "$1" in
    -i|--input)
      INPUT_FILE="$2"
      INPUT_FILE_SPECIFIED=1
      shift 2
      ;;
    -o|--output)
      OUTPUT_FILE="$2"
      OUTPUT_FILE_SPECIFIED=1
      shift 2
      ;;
    -f|--format)
      FORMAT="$2"
      shift 2
      ;;
    --title)
      TITLE="$2"
      shift 2
      ;;
    --no-title)
      NO_TITLE=1
      shift 1
      ;;
    --subtitle)
      SUBTITLE="$2"
      shift 2
      ;;
    --no-subtitle)
      NO_SUBTITLE=1
      shift 1
      ;;
    --no-mask)
      MASK_FLAG="--no-mask"
      shift 1
      ;;
    --zoom)
      ZOOM_ARGS=("$2" "$3" "$4")
      shift 4
      ;;
    --max-depth)
      MAX_DEPTH="$2"
      shift 2
      ;;
    --max-orography)
      MAX_OROGRAPHY="$2"
      shift 2
      ;;
    --display|--show)
      DISPLAY_FLAG="--display"
      shift 1
      ;;
    --no-display)
      DISPLAY_FLAG="--no-display"
      shift 1
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Error: Unknown option: $1" >&2
      usage
      exit 1
      ;;
  esac
done

# Resolve INPUT_FILE and OUTPUT_FILE relative to ORIG_DIR if explicitly specified by user input
if [ "$INPUT_FILE_SPECIFIED" -eq 1 ] && [[ "$INPUT_FILE" != /* ]]; then
  INPUT_FILE="${ORIG_DIR}/${INPUT_FILE}"
fi

if [ "$OUTPUT_FILE_SPECIFIED" -eq 1 ] && [[ "$OUTPUT_FILE" != /* ]]; then
  OUTPUT_FILE="${ORIG_DIR}/${OUTPUT_FILE}"
fi

echo "========================================================================"
echo " WAVEWATCH III / IV Grid Plotting Tool"
echo "========================================================================"

# 1. Check Input Dataset Availability
echo "[Step 1/3] Checking input dataset availability..."
if [ ! -f "$INPUT_FILE" ] && \
   [ ! -f "${INPUT_FILE}.nc" ] && \
   [ ! -f "${INPUT_FILE}_ugrid.nc" ] && \
   [ ! -f "${INPUT_FILE}_coards.nc" ] && \
   [ ! -f "${INPUT_FILE}.depth_ascii" ] && \
   [ ! -f "${INPUT_FILE}.meta" ]; then
  echo "Error: Input grid dataset file or prefix '${INPUT_FILE}' was not found." >&2
  echo "Please generate grid dataset files first by running:" >&2
  echo "  ./run_gridgen.sh" >&2
  exit 1
fi

# 2. Check Python Environment
echo "[Step 2/3] Validating Python environment and dependencies..."
if ! command -v python3 &> /dev/null; then
  echo "Error: 'python3' interpreter was not found in PATH." >&2
  exit 1
fi

if ! python3 -c "import numpy, matplotlib, xarray" &> /dev/null; then
  echo "Error: Required Python dependencies (numpy, matplotlib, xarray) are missing." >&2
  echo "Please install dependencies into your environment:" >&2
  echo "  pip install -e ." >&2
  exit 1
fi

# Build argument list
CMD_ARGS=(--input "$INPUT_FILE" --format "$FORMAT" "$DISPLAY_FLAG")

if [ "$NO_TITLE" -eq 1 ]; then
  CMD_ARGS+=(--no-title)
elif [ -n "$TITLE" ]; then
  CMD_ARGS+=(--title "$TITLE")
fi

if [ "$NO_SUBTITLE" -eq 1 ]; then
  CMD_ARGS+=(--no-subtitle)
elif [ -n "$SUBTITLE" ]; then
  CMD_ARGS+=(--subtitle "$SUBTITLE")
fi

if [ -n "$MASK_FLAG" ]; then
  CMD_ARGS+=("$MASK_FLAG")
fi

if [ ${#ZOOM_ARGS[@]} -gt 0 ]; then
  CMD_ARGS+=(--zoom "${ZOOM_ARGS[@]}")
fi

if [ -n "$MAX_DEPTH" ]; then
  CMD_ARGS+=(--max-depth "$MAX_DEPTH")
fi

if [ -n "$MAX_OROGRAPHY" ]; then
  CMD_ARGS+=(--max-orography "$MAX_OROGRAPHY")
fi

if [ -n "$OUTPUT_FILE" ]; then
  CMD_ARGS+=(--output "$OUTPUT_FILE")
fi

# 3. Execute Visualization Module
echo "[Step 3/3] Executing grid visualization module for '${INPUT_FILE}' in format '${FORMAT}'..."
python3 -m gridgen.vis "${CMD_ARGS[@]}"

echo "Plot generation finished successfully."
