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
# @date Update: 2026-10-06
#
# Shell driver script to generate graphical grid and obstruction plots in GIF format.

set -euo pipefail

ORIG_DIR="$(pwd)"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"
export PYTHONPATH="${SCRIPT_DIR}:${PYTHONPATH:-}"

INPUT_FILE="ww4_grid_ugrid.nc"
OUTPUT_FILE=""
FORMAT="jpg"
TITLE="WAVEWATCH IV Grid & Obstructions"
DISPLAY_FLAG="--display"

INPUT_FILE_SPECIFIED=0
OUTPUT_FILE_SPECIFIED=0

usage() {
  cat << 'EOF'
Usage: ./plot_grid.sh [OPTIONS]

Utility script to graphically display resulting WAVEWATCH III / IV grids and obstructions.

Options:
  -i, --input PATH       Input dataset file path (_ugrid.nc, _coards.nc, _ugrid.zarr, or ASCII prefix) (default: ww4_grid_ugrid.nc)
  -o, --output PATH      Output plot image file path (default: <GRIDNAME>.<format>)
  -f, --format FORMAT    Output graphic format: jpg, png, pdf, eps, or gif (default: jpg)
  --title TITLE          Custom figure title (default: WAVEWATCH IV Grid & Obstructions)
  --display              Display figure window interactively (default: enabled)
  --no-display           Disable interactive figure window display
  -h, --help             Display this help message and exit

Description:
  This script executes the Python grid visualization module (`gridgen.vis`)
  to produce multi-panel plots of bathymetry depth, land-sea mask, and
  sub-grid directional obstruction factors (sx, sy) in JPG, PNG, PDF, EPS, or GIF formats.
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
echo " WAVEWATCH III / IV Grid & Obstruction Plotting Tool"
echo "========================================================================"

# 1. Check Python Environment
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
CMD_ARGS=(--input "$INPUT_FILE" --format "$FORMAT" --title "$TITLE" "$DISPLAY_FLAG")
if [ -n "$OUTPUT_FILE" ]; then
  CMD_ARGS+=(--output "$OUTPUT_FILE")
fi

# 2. Execute Visualization Module
echo "Generating plot graphics for '${INPUT_FILE}' in format '${FORMAT}'..."
python3 -m gridgen.vis "${CMD_ARGS[@]}"

echo "Plot generation finished successfully."
