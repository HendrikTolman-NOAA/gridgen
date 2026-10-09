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
# @date Latest Update: 2026-10-09
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
LON_START=""
LON_END=""
LAT_START=""
LAT_END=""
CENTER_LON=""
CENTER_LAT=""
EXTENT_KM=""
RESOLUTION_KM=""
EXTENT_DEG=""
RESOLUTION_DEG=""
POLE_LON=""
POLE_LAT=""
NX="401"
NY="125"
CUSTOM_GRID=""
OUT_DIR="."
REF_DIR="${SCRIPT_DIR}/reference_data"
CLEANUP=0

OUT_DIR_SPECIFIED=0
REF_DIR_SPECIFIED=0

usage() {
  cat << 'EOF'
Usage: ./run_gridgen.sh [OPTIONS]

Utility script to manage and execute WAVEWATCH III / IV Python grid generation.

1. General & Dimension Options (Common to all grid options):
  --nx NX                Discrete grid dimension NX (default: 401) [Optional]
  --ny NY                Discrete grid dimension NY (default: 125) [Optional]
  -n, --name NAME        Grid prefix identifier (default: ww4_grid) [Optional]
  -g, --grid-type TYPE   Grid type: regular, stereographic, custom
                         (default: regular) [Optional]
  -o, --out-dir DIR      Output directory for grid files (default: .) [Optional]
  -r, --ref-dir DIR      Reference data directory (default: ./reference_data)
                         [Optional]
  -c, --clean, --cleanup Remove generated grid files and graphics for NAME
  -h, --help             Display this help message and exit

2. Regular Grid Parameters (--grid-type regular):
  --lon-start LON        [Mandatory] Lower-left corner longitude in degrees
  --lat-start LAT        [Mandatory] Lower-left corner latitude in degrees
  --lon-end LON          [Mandatory] Upper-right corner longitude in degrees
  --lat-end LAT          [Mandatory] Upper-right corner latitude in degrees
  --pole-lon LON         [Optional] Rotated north pole longitude (degrees)
  --pole-lat LAT         [Optional] Rotated north pole latitude (degrees)

3. Stereographic Grid Parameters (--grid-type stereographic):
  --center-lon LON       [Mandatory] Projection center longitude in degrees
  --center-lat LAT       [Mandatory] Projection center latitude in degrees
  --extent-km KM         [Mandatory if --extent-deg omitted] Half-width in km
  --resolution-km KM     [Optional] Grid resolution in kilometers
  --extent-deg DEG       [Mandatory if --extent-km omitted] Half-width in deg
  --resolution-deg DEG   [Optional] Grid resolution in arc degrees

4. Custom Grid Parameters (--grid-type custom):
  --custom-grid FILE     [Mandatory] Path to custom layout file
                         (.nc, .npz, .npy, .mat, .dat, .txt, .csv)

Description:
  This script checks that reference bathymetry and shoreline datasets are
  present in the reference data directory before invoking Python gridgen.

  Exported formats include:
    1. Legacy WW3 ASCII grid (.depth_ascii, .maskorig_ascii, .obstr_lev1)
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
    --lon-start|--LON-START)
      LON_START="$2"
      shift 2
      ;;
    --lon-end|--LON-END)
      LON_END="$2"
      shift 2
      ;;
    --lat-start|--LAT-START)
      LAT_START="$2"
      shift 2
      ;;
    --lat-end|--LAT-END)
      LAT_END="$2"
      shift 2
      ;;
    --center-lon|--CENTER-LON)
      CENTER_LON="$2"
      shift 2
      ;;
    --center-lat|--CENTER-LAT)
      CENTER_LAT="$2"
      shift 2
      ;;
    --extent-km|--EXTENT-KM)
      EXTENT_KM="$2"
      shift 2
      ;;
    --resolution-km|--RESOLUTION-KM)
      RESOLUTION_KM="$2"
      shift 2
      ;;
    --extent-deg|--EXTENT-DEG)
      EXTENT_DEG="$2"
      shift 2
      ;;
    --resolution-deg|--RESOLUTION-DEG)
      RESOLUTION_DEG="$2"
      shift 2
      ;;
    --pole-lon|--POLE-LON)
      POLE_LON="$2"
      shift 2
      ;;
    --pole-lat|--POLE-LAT)
      POLE_LAT="$2"
      shift 2
      ;;
    --nx|--NX)
      NX="$2"
      shift 2
      ;;
    --ny|--NY)
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

# Display verbose input parameter summary for active grid configuration
echo "Grid Configuration Summary:"
echo "  Prefix Name          : ${NAME}"
echo "  Grid Type            : ${GRID_TYPE}"
echo "  Output Directory     : ${OUT_DIR}"
echo "  Reference Directory  : ${REF_DIR}"
if [ -n "$NX" ]; then echo "  NX (Lon/X Points)    : ${NX}"; fi
if [ -n "$NY" ]; then echo "  NY (Lat/Y Points)    : ${NY}"; fi

case "${GRID_TYPE}" in
  regular)
    if [ -n "$LON_START" ]; then echo "  LON_START (Lower-Left): ${LON_START} deg"; fi
    if [ -n "$LAT_START" ]; then echo "  LAT_START (Lower-Left): ${LAT_START} deg"; fi
    if [ -n "$LON_END" ]; then echo "  LON_END (Upper-Right)  : ${LON_END} deg"; fi
    if [ -n "$LAT_END" ]; then echo "  LAT_END (Upper-Right)  : ${LAT_END} deg"; fi
    if [ -n "$POLE_LON" ]; then echo "  POLE_LON             : ${POLE_LON} deg"; fi
    if [ -n "$POLE_LAT" ]; then echo "  POLE_LAT             : ${POLE_LAT} deg"; fi
    ;;
  stereographic)
    if [ -n "$CENTER_LON" ]; then echo "  CENTER_LON (Proj)    : ${CENTER_LON} deg"; fi
    if [ -n "$CENTER_LAT" ]; then echo "  CENTER_LAT (Proj)    : ${CENTER_LAT} deg"; fi
    if [ -n "$EXTENT_KM" ]; then echo "  EXTENT_KM            : ${EXTENT_KM} km"; fi
    if [ -n "$RESOLUTION_KM" ]; then echo "  RESOLUTION_KM        : ${RESOLUTION_KM} km"; fi
    if [ -n "$EXTENT_DEG" ]; then echo "  EXTENT_DEG           : ${EXTENT_DEG} deg"; fi
    if [ -n "$RESOLUTION_DEG" ]; then echo "  RESOLUTION_DEG       : ${RESOLUTION_DEG} deg"; fi
    ;;
  custom)
    if [ -n "$CUSTOM_GRID" ]; then echo "  Custom Grid File     : ${CUSTOM_GRID}"; fi
    ;;
esac
echo "========================================================================"

# Check for cleanup option
if [ "$CLEANUP" -eq 1 ]; then
  echo "Cleaning up generated grid files and graphics files for prefix '${NAME}' in directory '${OUT_DIR}'..."
  rm -rf "${OUT_DIR}/${NAME}.depth_ascii" \
         "${OUT_DIR}/${NAME}.maskorig_ascii" \
         "${OUT_DIR}/${NAME}.obstr_lev1" \
         "${OUT_DIR}/${NAME}.meta" \
         "${OUT_DIR}/${NAME}_coards.nc" \
         "${OUT_DIR}/${NAME}_ugrid.nc" \
         "${OUT_DIR}/${NAME}.jpg" \
         "${OUT_DIR}/${NAME}.jpeg" \
         "${OUT_DIR}/${NAME}.png" \
         "${OUT_DIR}/${NAME}.pdf" \
         "${OUT_DIR}/${NAME}.eps" \
         "${OUT_DIR}/${NAME}.gif" \
         "${OUT_DIR}/${NAME}"*.jpg \
         "${OUT_DIR}/${NAME}"*.jpeg \
         "${OUT_DIR}/${NAME}"*.png \
         "${OUT_DIR}/${NAME}"*.pdf \
         "${OUT_DIR}/${NAME}"*.eps \
         "${OUT_DIR}/${NAME}"*.gif
  echo "Cleanup finished successfully."
  exit 0
fi

# 1. Check Reference Data Directory
if [ ! -d "$REF_DIR" ] || [ -z "$(ls -A "$REF_DIR"/*.nc "$REF_DIR"/*.tif 2>/dev/null)" ]; then
  echo "Error: Reference bathymetry dataset files were not found in '${REF_DIR}'." >&2
  echo "Please populate reference data first by running:" >&2
  echo "  ./populate_reference_data.sh" >&2
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
  --out-dir "$OUT_DIR"
  --ref-dir "$REF_DIR"
)

if [ -n "$LON_START" ]; then CMD_ARGS+=(--lon-start "$LON_START"); fi
if [ -n "$LON_END" ]; then CMD_ARGS+=(--lon-end "$LON_END"); fi
if [ -n "$LAT_START" ]; then CMD_ARGS+=(--lat-start "$LAT_START"); fi
if [ -n "$LAT_END" ]; then CMD_ARGS+=(--lat-end "$LAT_END"); fi
if [ -n "$CENTER_LON" ]; then CMD_ARGS+=(--center-lon "$CENTER_LON"); fi
if [ -n "$CENTER_LAT" ]; then CMD_ARGS+=(--center-lat "$CENTER_LAT"); fi
if [ -n "$EXTENT_KM" ]; then CMD_ARGS+=(--extent-km "$EXTENT_KM"); fi
if [ -n "$RESOLUTION_KM" ]; then CMD_ARGS+=(--resolution-km "$RESOLUTION_KM"); fi
if [ -n "$EXTENT_DEG" ]; then CMD_ARGS+=(--extent-deg "$EXTENT_DEG"); fi
if [ -n "$RESOLUTION_DEG" ]; then CMD_ARGS+=(--resolution-deg "$RESOLUTION_DEG"); fi
if [ -n "$POLE_LON" ]; then CMD_ARGS+=(--pole-lon "$POLE_LON"); fi
if [ -n "$POLE_LAT" ]; then CMD_ARGS+=(--pole-lat "$POLE_LAT"); fi
if [ -n "$NX" ]; then CMD_ARGS+=(--nx "$NX"); fi
if [ -n "$NY" ]; then CMD_ARGS+=(--ny "$NY"); fi
if [ -n "$CUSTOM_GRID" ]; then CMD_ARGS+=(--custom-grid "$CUSTOM_GRID"); fi

python3 -m gridgen.cli "${CMD_ARGS[@]}"

echo ""
echo "Execution finished successfully."
