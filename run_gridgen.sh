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
# @date Latest Update: 2026-10-08
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
SX=""
SY=""
LON_START=""
LON_END=""
LAT_START=""
LAT_END=""
CENTER_LON=""
CENTER_LAT=""
LAT_1=""
LAT_2=""
EXTENT_KM=""
RESOLUTION_KM=""
POLE_LON=""
POLE_LAT=""
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

Utility script to manage and execute WAVEWATCH III / IV Python grid generation.

1. General & Dimension Options (Common to all grid types):
  --nx NX                [Mandatory/Recommended] Grid dimension NX (X points)
  --ny NY                [Mandatory/Recommended] Grid dimension NY (Y points)
  -n, --name NAME        Grid prefix identifier (default: ww4_grid)
  -g, --grid-type TYPE   Grid type: regular, stereographic, lambert_conformal,
                         rotated_pole, custom (default: regular)
  -o, --out-dir DIR      Output directory for generated grid files (default: .)
  -r, --ref-dir DIR      Reference data directory (default: ./reference_data)
  -c, --clean, --cleanup Remove generated grid files and graphics for NAME
  -h, --help             Display this help message and exit

2. Regular Grid Parameters (--grid-type regular):
  --sx, --dx SX          Grid longitude increment/spacing in degrees (SX/DX)
  --sy, --dy SY          Grid latitude increment/spacing in degrees (SY/DY)
  --lon-start LON        Lower-left corner longitude in degrees
  --lat-start LAT        Lower-left corner latitude in degrees
  --lon-end LON          Upper-right corner longitude in degrees
  --lat-end LAT          Upper-right corner latitude in degrees

3. Rotated Pole Grid Parameters (--grid-type rotated_pole):
  --pole-lon LON         [Mandatory] Rotated north pole longitude (degrees)
  --pole-lat LAT         [Mandatory] Rotated north pole latitude (degrees)

4. Stereographic Grid Parameters (--grid-type stereographic):
  --center-lon LON       [Mandatory] Projection center longitude in degrees
  --center-lat LAT       [Mandatory] Projection center latitude in degrees
  --extent-km KM         [Mandatory] Half-width domain extent in kilometers
  --resolution-km KM     [Mandatory] Grid resolution in kilometers

5. Lambert Conformal Conic Parameters (--grid-type lambert_conformal):
  --lat-1 LAT            [Mandatory] First standard parallel in degrees
  --lat-2 LAT            [Mandatory] Second standard parallel in degrees

6. Custom Grid Parameters (--grid-type custom):
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
    --sx|--dx)
      SX="$2"
      shift 2
      ;;
    --sy|--dy)
      SY="$2"
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

# Display verbose input parameter summary for active grid configuration
echo "Grid Configuration Summary:"
echo "  Prefix Name          : ${NAME}"
echo "  Grid Type            : ${GRID_TYPE}"
echo "  Output Directory     : ${OUT_DIR}"
echo "  Reference Directory  : ${REF_DIR}"
if [ -n "$NX" ]; then echo "  NX (Lon/X Points)    : ${NX}"; fi
if [ -n "$NY" ]; then echo "  NY (Lat/Y Points)    : ${NY}"; fi

case "${GRID_TYPE}" in
  regular|latlon|rectilinear)
    if [ -n "$SX" ]; then echo "  SX / DX Spacing      : ${SX} deg"; fi
    if [ -n "$SY" ]; then echo "  SY / DY Spacing      : ${SY} deg"; fi
    if [ -n "$LON_START" ]; then echo "  Lon Start (Lower-Left): ${LON_START} deg"; fi
    if [ -n "$LAT_START" ]; then echo "  Lat Start (Lower-Left): ${LAT_START} deg"; fi
    if [ -n "$LON_END" ]; then echo "  Lon End (Upper-Right)  : ${LON_END} deg"; fi
    if [ -n "$LAT_END" ]; then echo "  Lat End (Upper-Right)  : ${LAT_END} deg"; fi
    if [ -n "$CENTER_LON" ]; then echo "  Center Lon (Anchor)   : ${CENTER_LON} deg"; fi
    if [ -n "$CENTER_LAT" ]; then echo "  Center Lat (Anchor)   : ${CENTER_LAT} deg"; fi
    ;;
  rotated_pole|curvilinear)
    if [ -n "$POLE_LON" ]; then echo "  Rotated Pole Lon     : ${POLE_LON} deg"; fi
    if [ -n "$POLE_LAT" ]; then echo "  Rotated Pole Lat     : ${POLE_LAT} deg"; fi
    if [ -n "$SX" ]; then echo "  SX Spacing (Rotated) : ${SX} deg"; fi
    if [ -n "$SY" ]; then echo "  SY Spacing (Rotated) : ${SY} deg"; fi
    if [ -n "$LON_START" ]; then echo "  Lon Start (Rotated)  : ${LON_START} deg"; fi
    if [ -n "$LAT_START" ]; then echo "  Lat Start (Rotated)  : ${LAT_START} deg"; fi
    if [ -n "$CENTER_LON" ]; then echo "  Center Lon (Rotated) : ${CENTER_LON} deg"; fi
    if [ -n "$CENTER_LAT" ]; then echo "  Center Lat (Rotated) : ${CENTER_LAT} deg"; fi
    ;;
  stereographic|polar_stereographic)
    if [ -n "$CENTER_LON" ]; then echo "  Center Lon (Proj)    : ${CENTER_LON} deg"; fi
    if [ -n "$CENTER_LAT" ]; then echo "  Center Lat (Proj)    : ${CENTER_LAT} deg"; fi
    if [ -n "$EXTENT_KM" ]; then echo "  Domain Extent        : ${EXTENT_KM} km"; fi
    if [ -n "$RESOLUTION_KM" ]; then echo "  Grid Resolution      : ${RESOLUTION_KM} km"; fi
    ;;
  lambert_conformal|lambert)
    if [ -n "$CENTER_LON" ]; then echo "  Center Lon (Proj)    : ${CENTER_LON} deg"; fi
    if [ -n "$CENTER_LAT" ]; then echo "  Center Lat (Proj)    : ${CENTER_LAT} deg"; fi
    if [ -n "$LAT_1" ]; then echo "  Standard Parallel 1  : ${LAT_1} deg"; fi
    if [ -n "$LAT_2" ]; then echo "  Standard Parallel 2  : ${LAT_2} deg"; fi
    if [ -n "$EXTENT_KM" ]; then echo "  Domain Extent        : ${EXTENT_KM} km"; fi
    if [ -n "$RESOLUTION_KM" ]; then echo "  Grid Resolution      : ${RESOLUTION_KM} km"; fi
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

if [ -n "$SX" ]; then CMD_ARGS+=(--sx "$SX"); fi
if [ -n "$SY" ]; then CMD_ARGS+=(--sy "$SY"); fi
if [ -n "$LON_START" ]; then CMD_ARGS+=(--lon-start "$LON_START"); fi
if [ -n "$LON_END" ]; then CMD_ARGS+=(--lon-end "$LON_END"); fi
if [ -n "$LAT_START" ]; then CMD_ARGS+=(--lat-start "$LAT_START"); fi
if [ -n "$LAT_END" ]; then CMD_ARGS+=(--lat-end "$LAT_END"); fi
if [ -n "$CENTER_LON" ]; then CMD_ARGS+=(--center-lon "$CENTER_LON"); fi
if [ -n "$CENTER_LAT" ]; then CMD_ARGS+=(--center-lat "$CENTER_LAT"); fi
if [ -n "$LAT_1" ]; then CMD_ARGS+=(--lat-1 "$LAT_1"); fi
if [ -n "$LAT_2" ]; then CMD_ARGS+=(--lat-2 "$LAT_2"); fi
if [ -n "$EXTENT_KM" ]; then CMD_ARGS+=(--extent-km "$EXTENT_KM"); fi
if [ -n "$RESOLUTION_KM" ]; then CMD_ARGS+=(--resolution-km "$RESOLUTION_KM"); fi
if [ -n "$POLE_LON" ]; then CMD_ARGS+=(--pole-lon "$POLE_LON"); fi
if [ -n "$POLE_LAT" ]; then CMD_ARGS+=(--pole-lat "$POLE_LAT"); fi
if [ -n "$NX" ]; then CMD_ARGS+=(--nx "$NX"); fi
if [ -n "$NY" ]; then CMD_ARGS+=(--ny "$NY"); fi
if [ -n "$CUSTOM_GRID" ]; then CMD_ARGS+=(--custom-grid "$CUSTOM_GRID"); fi

python3 -m gridgen.cli "${CMD_ARGS[@]}"

echo ""
echo "Execution finished successfully."
