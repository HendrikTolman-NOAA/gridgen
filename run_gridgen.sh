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
# @date Initial: 2026-10-02
# @date Latest Update: 2026-10-07
#
# Utility tool to manage running WAVEWATCH grid generation Python tools
# after reference data files have been populated in reference_data/.

set -euo pipefail

ORIG_DIR="$(pwd)"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"
export PYTHONPATH="${SCRIPT_DIR}:${PYTHONPATH:-}"

# Default Configuration
NAME="ww4_grid"
GRID_TYPE="regular"
DX="0.25"
DY="0.25"
LON_START="140.0"
LON_END="160.0"
LAT_START="44.0"
LAT_END="54.0"
CENTER_LON="0.0"
CENTER_LAT="90.0"
LAT_1="30.0"
LAT_2="60.0"
EXTENT_KM="2000.0"
RESOLUTION_KM="50.0"
POLE_LON="180.0"
POLE_LAT="60.0"
NX=""
NY=""
CUSTOM_GRID=""
OUT_DIR="."
REF_DIR="${SCRIPT_DIR}/reference_data"
CLEANUP=0

OUT_DIR_SPECIFIED=0
REF_DIR_SPECIFIED=0

usage() {
  cat << 'EOF'
Usage: ./run_gridgen.sh [OPTIONS]

Utility script to manage and execute WAVEWATCH III / IV Python grid generation tools.

Options:
  -n, --name NAME          Grid prefix identifier (default: ww4_grid)
  -g, --grid-type TYPE     Grid type: regular, stereographic, lambert_conformal, rotated_pole, custom (default: regular)
  --dx DX                  Longitude grid resolution increment in degrees (default: 0.25)
  --dy DY                  Latitude grid resolution increment in degrees (default: 0.25)
  --lon-start LON          Minimum longitude in degrees (default: 140.0)
  --lon-end LON            Maximum longitude in degrees (default: 160.0)
  --lat-start LAT          Minimum latitude in degrees (default: 44.0)
  --lat-end LAT            Maximum latitude in degrees (default: 54.0)
  --center-lon LON         Center longitude for stereographic/Lambert projection (default: 0.0)
  --center-lat LAT         Center latitude for stereographic/Lambert projection (default: 90.0)
  --lat-1 LAT              First standard parallel for Lambert conformal projection (default: 30.0)
  --lat-2 LAT              Second standard parallel for Lambert conformal projection (default: 60.0)
  --extent-km KM           Half-width domain extent in km for stereographic/Lambert grid (default: 2000.0)
  --resolution-km KM       Grid resolution in km for stereographic/Lambert grid (default: 50.0)
  --pole-lon LON           Rotated pole longitude for rotated_pole projection (default: 180.0)
  --pole-lat LAT           Rotated pole latitude for rotated_pole projection (default: 60.0)
  --nx NX                  Number of longitude/x grid points
  --ny NY                  Number of latitude/y grid points
  --custom-grid FILE       Path to custom grid layout file (.nc, .npz, .npy, .mat, .dat, .txt, .csv)
  -o, --out-dir DIR        Output directory for generated grid files (default: .)
  -r, --ref-dir DIR        Reference data directory (default: ./reference_data)
  -c, --clean, --cleanup   Remove generated grid files for NAME from output directory
  -h, --help               Display this help message and exit

Description:
  This script checks that reference bathymetry and shoreline datasets are present
  in the reference data directory before invoking the Python grid generation
  pipeline (`ww4gridgen` / `gridgen.cli`).

  Exported formats include:
    1. Legacy WW3 ASCII grid (.depth_ascii, .maskorig_ascii, .obstr_lev1, .meta)
    2. Legacy GMT/NetCDF COARDS grid (_coards.nc)
    3. WW4 NetCDF-UGRID 1.0 grid (_ugrid.nc)
EOF
}

# Parse Arguments
while [[ $# -gt 0 ]]; do
  case "$1" in
    -n|--name)
      NAME="$2"
      shift 2
      ;;
    -g|--grid-type)
      GRID_TYPE="$2"
      shift 2
      ;;
    --dx)
      DX="$2"
      shift 2
      ;;
    --dy)
      DY="$2"
      shift 2
      ;;
    --lon-start)
      LON_START="$2"
      shift 2
      ;;
    --lon-end)
      LON_END="$2"
      shift 2
      ;;
    --lat-start)
      LAT_START="$2"
      shift 2
      ;;
    --lat-end)
      LAT_END="$2"
      shift 2
      ;;
    --center-lon)
      CENTER_LON="$2"
      shift 2
      ;;
    --center-lat)
      CENTER_LAT="$2"
      shift 2
      ;;
    --lat-1)
      LAT_1="$2"
      shift 2
      ;;
    --lat-2)
      LAT_2="$2"
      shift 2
      ;;
    --extent-km)
      EXTENT_KM="$2"
      shift 2
      ;;
    --resolution-km)
      RESOLUTION_KM="$2"
      shift 2
      ;;
    --pole-lon)
      POLE_LON="$2"
      shift 2
      ;;
    --pole-lat)
      POLE_LAT="$2"
      shift 2
      ;;
    --nx)
      NX="$2"
      shift 2
      ;;
    --ny)
      NY="$2"
      shift 2
      ;;
    --custom-grid)
      CUSTOM_GRID="$2"
      shift 2
      ;;
    -o|--out-dir)
      OUT_DIR="$2"
      OUT_DIR_SPECIFIED=1
      shift 2
      ;;
    -r|--ref-dir)
      REF_DIR="$2"
      REF_DIR_SPECIFIED=1
      shift 2
      ;;
    -c|--clean|--cleanup)
      CLEANUP=1
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

# Resolve OUT_DIR and REF_DIR relative to ORIG_DIR if explicitly specified by user input
if [ "$OUT_DIR_SPECIFIED" -eq 1 ]; then
  if [[ "$OUT_DIR" != /* ]]; then
    OUT_DIR="${ORIG_DIR}/${OUT_DIR}"
  fi
else
  OUT_DIR="."
fi

if [ "$REF_DIR_SPECIFIED" -eq 1 ]; then
  if [[ "$REF_DIR" != /* ]]; then
    REF_DIR="${ORIG_DIR}/${REF_DIR}"
  fi
else
  REF_DIR="${SCRIPT_DIR}/reference_data"
fi

echo "========================================================================"
echo " WAVEWATCH III / IV Python Grid Generation Driver"
echo "========================================================================"

# Check for cleanup option
if [ "$CLEANUP" -eq 1 ]; then
  echo "Cleaning up generated grid files for prefix '${NAME}' in directory '${OUT_DIR}'..."
  rm -rf "${OUT_DIR}/${NAME}.depth_ascii" \
         "${OUT_DIR}/${NAME}.maskorig_ascii" \
         "${OUT_DIR}/${NAME}.obstr_lev1" \
         "${OUT_DIR}/${NAME}.meta" \
         "${OUT_DIR}/${NAME}_coards.nc" \
         "${OUT_DIR}/${NAME}_ugrid.nc" \
         "${OUT_DIR}/${NAME}.jpg" \
         "${OUT_DIR}/${NAME}.png" \
         "${OUT_DIR}/${NAME}.pdf" \
         "${OUT_DIR}/${NAME}.eps" \
         "${OUT_DIR}/${NAME}.gif"
  echo "Cleanup finished successfully."
  exit 0
fi

# 1. Check Reference Data Directory
if [ ! -d "$REF_DIR" ] || [ -z "$(ls -A "$REF_DIR"/*.nc "$REF_DIR"/*.tif 2>/dev/null)" ]; then
  echo "Error: Reference bathymetry dataset files were not found in '${REF_DIR}'." >&2
  echo "Please populate reference data first by running:" >&2
  echo "  ./populate_reference_data.sh --target-dir '${REF_DIR}'" >&2
  exit 1
fi

# Ensure output directory exists
mkdir -p "$OUT_DIR"

# 2. Check Python Environment
if ! command -v python3 &> /dev/null; then
  echo "Error: 'python3' interpreter was not found in PATH." >&2
  exit 1
fi

if ! python3 -c "import numpy, scipy, xarray, netCDF4, shapely" &> /dev/null; then
  echo "Error: Required Python dependencies (numpy, scipy, xarray, netCDF4, shapely) are missing in environment '$(command -v python3)'." >&2
  echo "Please install dependencies into your Python environment:" >&2
  echo "  pip install -e ." >&2
  echo "or activate a Python environment/venv with required packages installed." >&2
  exit 1
fi

# 3. Execute Python Gridgen CLI
echo "Launching Python grid generation pipeline for '${NAME}'..."
CMD_ARGS=(
  --name "$NAME"
  --grid-type "$GRID_TYPE"
  --dx "$DX"
  --dy "$DY"
  --lon-start "$LON_START"
  --lon-end "$LON_END"
  --lat-start "$LAT_START"
  --lat-end "$LAT_END"
  --center-lon "$CENTER_LON"
  --center-lat "$CENTER_LAT"
  --lat-1 "$LAT_1"
  --lat-2 "$LAT_2"
  --extent-km "$EXTENT_KM"
  --resolution-km "$RESOLUTION_KM"
  --pole-lon "$POLE_LON"
  --pole-lat "$POLE_LAT"
  --out-dir "$OUT_DIR"
  --ref-dir "$REF_DIR"
)

if [ -n "$NX" ]; then
  CMD_ARGS+=(--nx "$NX")
fi
if [ -n "$NY" ]; then
  CMD_ARGS+=(--ny "$NY")
fi
if [ -n "$CUSTOM_GRID" ]; then
  CMD_ARGS+=(--custom-grid "$CUSTOM_GRID")
fi

python3 -m gridgen.cli "${CMD_ARGS[@]}"

echo ""
echo "Execution finished successfully."
