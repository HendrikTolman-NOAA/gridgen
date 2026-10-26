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
# @date Latest Update: 2026-10-23
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
LON_START="20.0"
LON_END="379.75"
LAT_START="-75.0"
LAT_END="75.0"
SX=""
SY=""
CENTER_LON=""
CENTER_LAT=""
EXTENT_KM=""
EXTENT_DEG=""
ROTATION=""
POLE_LON=""
POLE_LAT=""
NX="1440"
NY="601"
GLOBAL_CLOSURE=0
CUSTOM_GRID=""
BATHY_SOURCE="etopo2"
BOUNDARY_POINTS=0
CUT_OFF="0.1"
LAKE_MIN_POINTS="15"
LAKE_MIN_FRACTION="0.0005"
LEGACY=0
LOCAL_POLYGONS=0
NO_USER_POLYGONS=0
ALL_POLYGONS=0
USER_POLYGONS_FLAG=""
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
  --nx NX                Discrete grid dimension NX (default: 1440) [Optional]
  --ny NY                Discrete grid dimension NY (default: 601) [Optional]
  -n, --name NAME        Grid prefix identifier (default: ww4_grid) [Optional]
  -g, --grid-type TYPE   Grid type: regular, stereographic, custom
                         (default: regular) [Optional]
  --bathy-source SOURCE  Bathymetry reference source (default: etopo2) [Optional]
  --boundary-points      Define input boundary cells (mask value 2) [Optional]
  --cut-off DEPTH, --cutoff-depth DEPTH
                         Cut-off depth in meters to distinguish wet vs. dry cells
                         (default: 0.1) [Optional]
  --lake-min-points PTS  Minimum points for a lake to be retained (default: 15) [Optional]
  --lake-min-fraction FRAC
                         Minimum grid fraction for a lake to be retained
                         (default: 0.0005 [0.05%]) [Optional]
  --legacy               Export legacy ASCII and COARDS NetCDF files [Optional]
  --local-polygons       Use optional user coastal polygon files from local directory (.)
                         instead of gridgen_data [Optional]
  --no-user-polygons     Disable loading user coastal polygons [Optional]
  --all-polygons         Apply all coastal polygons independent of switch values [Optional]
  --user-polygons-flag FILE, --user-flag FILE, --flag-file FILE
                         Custom user polygon switch control flag file path or name
                         (default: user_polygons.flag) [Optional]
  -o, --out-dir DIR      Output directory for grid files (default: .) [Optional]
  -r, --ref-dir DIR      Reference data directory (default: ./reference_data)
                         [Optional]
  -c, --clean, --cleanup Remove generated grid files and graphics for NAME
  -h, --help             Display this help message and exit

2. Regular Grid Parameters (--grid-type regular):
  --lon-start LON        Lower-left longitude in deg (default: 20.0) [Optional]
  --lat-start LAT        Lower-left latitude in deg (default: -75.0) [Optional]
  --lon-end LON          Upper-right longitude in deg (default: 379.75) [Optional]
  --lat-end LAT          Upper-right latitude in deg (default: 75.0) [Optional]
  --sx SX                Longitude increment in deg [Optional]
  --sy SY                Latitude increment in deg [Optional]
  --global-closure       Create traditional regular grid with global closure
                         (sx = 360/NX, lon-end calculated) [Optional]
  --pole-lon LON         Rotated north pole longitude in deg (default: 0.0)
                         [Optional]
  --pole-lat LAT         Rotated north pole latitude in deg (default: 90.0)
                         [Optional]

3. Stereographic Grid Parameters (--grid-type stereographic):
  --center-lon LON       Projection center longitude in deg (default: 0.0)
                         [Optional]
  --center-lat LAT       Projection center latitude in deg (default: 90.0)
                         [Optional]
  --extent-km KM         Half-width extent in km (default: 1000.0) [Optional]
  --extent-deg DEG       Half-width extent in deg [Optional]
  --rotation DEG         Grid rotation angle in deg (default: 0.0) [Optional]

4. Custom Grid Parameters (--grid-type custom):
  --custom-grid FILE     Path to custom layout file [Mandatory for custom]
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
    --sx|--SX)
      SX="$2"
      shift 2
      ;;
    --sy|--SY)
      SY="$2"
      shift 2
      ;;
    --global-closure|--global|--global-grid)
      GLOBAL_CLOSURE=1
      shift 1
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
    --extent-deg|--EXTENT-DEG)
      EXTENT_DEG="$2"
      shift 2
      ;;
    --rotation|--ROTATION)
      ROTATION="$2"
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
    --bathy-source|--BATHY-SOURCE)
      BATHY_SOURCE="$2"
      shift 2
      ;;
    --boundary-points)
      BOUNDARY_POINTS=1
      shift 1
      ;;
    --cut-off|--cutoff-depth)
      CUT_OFF="$2"
      shift 2
      ;;
    --lake-min-points)
      LAKE_MIN_POINTS="$2"
      shift 2
      ;;
    --lake-min-fraction)
      LAKE_MIN_FRACTION="$2"
      shift 2
      ;;
    --legacy)
      LEGACY=1
      shift 1
      ;;
    --local-polygons)
      LOCAL_POLYGONS=1
      shift 1
      ;;
    --no-user-polygons)
      NO_USER_POLYGONS=1
      shift 1
      ;;
    --all-polygons|--all-user-polygons)
      ALL_POLYGONS=1
      shift 1
      ;;
    --user-polygons-flag|--user-flag|--flag-file)
      USER_POLYGONS_FLAG="$2"
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
  OUT_DIR="${SCRIPT_DIR}"
fi

if [ "$REF_DIR_SPECIFIED" -eq 1 ]; then
  if [[ "$REF_DIR" != /* ]]; then
    REF_DIR="${ORIG_DIR}/${REF_DIR}"
  fi
else
  REF_DIR="${SCRIPT_DIR}/reference_data"
fi


# Check for cleanup option
if [ "$CLEANUP" -eq 1 ]; then
  echo "========================================================================"
  echo " WAVEWATCH III / IV Python Grid Generation Driver"
  echo "========================================================================"
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

echo "========================================================================"
echo " WAVEWATCH III / IV Python Grid Generation Driver"
echo "========================================================================"

# Display verbose input parameter summary for active grid configuration
echo "Grid Configuration Summary:"
printf "  %-22s : %s\n" "Prefix Name" "${NAME}"
printf "  %-22s : %s\n" "Grid Type" "${GRID_TYPE}"
printf "  %-22s : %s\n" "Output Directory" "${OUT_DIR}"
printf "  %-22s : %s\n" "Reference Directory" "${REF_DIR}"
printf "  %-22s : %s\n" "Bathymetry Source" "${BATHY_SOURCE}"
if [ -n "$NX" ]; then printf "  %-22s : %s\n" "NX (Lon/X Points)" "${NX}"; fi
if [ -n "$NY" ]; then printf "  %-22s : %s\n" "NY (Lat/Y Points)" "${NY}"; fi

case "${GRID_TYPE}" in
  regular)
    if [ -n "$LON_START" ] && [ -n "$LAT_START" ] && [ -n "$NX" ] && [ -n "$NY" ]; then
      GRID_CALCS=$(awk -v lon_s="$LON_START" -v lon_e="$LON_END" -v lat_s="$LAT_START" -v lat_e="$LAT_END" -v sx_in="$SX" -v sy_in="$SY" -v nx="$NX" -v ny="$NY" -v is_global="$GLOBAL_CLOSURE" 'BEGIN {
        sx = sx_in;
        sy = sy_in;
        lon_end = lon_e;
        lat_end = lat_e;

        if (is_global == 1) {
          sx = 360.0 / nx;
          lon_end = lon_s + (nx - 1) * sx;
        } else {
          if (sx == "" && lon_end != "") { sx = (nx > 1) ? (lon_end - lon_s) / (nx - 1) : 0.0; }
          if (lon_end == "" && sx != "") { lon_end = lon_s + (nx - 1) * sx; }
        }

        if (sy == "" && lat_end != "") { sy = (ny > 1) ? (lat_end - lat_s) / (ny - 1) : 0.0; }
        if (lat_end == "" && sy != "") { lat_end = lat_s + (ny - 1) * sy; }

        sx_val = (sx != "") ? sx : 0.0;
        sy_val = (sy != "") ? sy : 0.0;
        span = nx * sx_val;
        diff = span - 360.0; if (diff < 0) diff = -diff;
        closure = (is_global == 1 || diff < 0.0001) ? "Yes" : "No";

        printf "SX=%.6f; SY=%.6f; LON_END=%.4f; LAT_END=%.4f; CLOSURE=%s;", sx_val, sy_val, lon_end, lat_end, closure
      }')
      eval "$GRID_CALCS"
    fi

    if [ -n "$LON_START" ]; then printf "  %-22s : %s deg\n" "LON_START (Lower-Left)" "${LON_START}"; fi
    if [ -n "$LAT_START" ]; then printf "  %-22s : %s deg\n" "LAT_START (Lower-Left)" "${LAT_START}"; fi
    if [ -n "$LON_END" ]; then printf "  %-22s : %s deg\n" "LON_END (Upper-Right)" "${LON_END}"; fi
    if [ -n "$LAT_END" ]; then printf "  %-22s : %s deg\n" "LAT_END (Upper-Right)" "${LAT_END}"; fi
    if [ -n "$POLE_LON" ]; then printf "  %-22s : %s deg\n" "POLE_LON" "${POLE_LON}"; fi
    if [ -n "$POLE_LAT" ]; then printf "  %-22s : %s deg\n" "POLE_LAT" "${POLE_LAT}"; fi
    if [ -n "$SX" ]; then printf "  %-22s : %s deg\n" "SX (Lon Increment)" "${SX}"; fi
    if [ -n "$SY" ]; then printf "  %-22s : %s deg\n" "SY (Lat Increment)" "${SY}"; fi
    if [ -n "${CLOSURE:-}" ]; then printf "  %-22s : %s\n" "Global Closure" "${CLOSURE}"; fi
    ;;
  stereographic)
    if [ -n "$CENTER_LON" ]; then printf "  %-22s : %s deg\n" "CENTER_LON (Proj)" "${CENTER_LON}"; fi
    if [ -n "$CENTER_LAT" ]; then printf "  %-22s : %s deg\n" "CENTER_LAT (Proj)" "${CENTER_LAT}"; fi
    if [ -n "$EXTENT_KM" ]; then printf "  %-22s : %s km\n" "EXTENT_KM" "${EXTENT_KM}"; fi
    if [ -n "$EXTENT_DEG" ]; then printf "  %-22s : %s deg\n" "EXTENT_DEG" "${EXTENT_DEG}"; fi
    if [ -n "$ROTATION" ]; then printf "  %-22s : %s deg\n" "ROTATION" "${ROTATION}"; fi
    ;;
  custom)
    if [ -n "$CUSTOM_GRID" ]; then printf "  %-22s : %s\n" "Custom Grid File" "${CUSTOM_GRID}"; fi
    ;;
esac
echo "========================================================================"

# 1. Check Reference Data Directory
echo "[Step 1/3] Checking reference data directory..."
if [ ! -d "$REF_DIR" ] || [ -z "$(ls -A "$REF_DIR"/*.nc "$REF_DIR"/*.tif 2>/dev/null)" ]; then
  echo "Error: Reference bathymetry dataset files were not found in '${REF_DIR}'." >&2
  echo "Please populate reference data first by running:" >&2
  echo "  ./populate_reference_data.sh" >&2
  exit 1
fi

# Ensure output directory exists
mkdir -p "$OUT_DIR"

# 2. Check Python Environment
echo "[Step 2/3] Validating Python environment and dependencies..."
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
echo "[Step 3/3] Launching Python grid generation pipeline for '${NAME}'..."
CMD_ARGS=(
  --name "$NAME"
  --grid-type "$GRID_TYPE"
  --out-dir "$OUT_DIR"
  --ref-dir "$REF_DIR"
  --bathy-source "$BATHY_SOURCE"
)

if [ -n "$LON_START" ]; then CMD_ARGS+=(--lon-start "$LON_START"); fi
if [ -n "$LON_END" ]; then CMD_ARGS+=(--lon-end "$LON_END"); fi
if [ -n "$LAT_START" ]; then CMD_ARGS+=(--lat-start "$LAT_START"); fi
if [ -n "$LAT_END" ]; then CMD_ARGS+=(--lat-end "$LAT_END"); fi
if [ -n "$SX" ]; then CMD_ARGS+=(--sx "$SX"); fi
if [ -n "$SY" ]; then CMD_ARGS+=(--sy "$SY"); fi
if [ -n "$CENTER_LON" ]; then CMD_ARGS+=(--center-lon "$CENTER_LON"); fi
if [ -n "$CENTER_LAT" ]; then CMD_ARGS+=(--center-lat "$CENTER_LAT"); fi
if [ -n "$EXTENT_KM" ]; then CMD_ARGS+=(--extent-km "$EXTENT_KM"); fi
if [ -n "$EXTENT_DEG" ]; then CMD_ARGS+=(--extent-deg "$EXTENT_DEG"); fi
if [ -n "$ROTATION" ]; then CMD_ARGS+=(--rotation "$ROTATION"); fi
if [ -n "$POLE_LON" ]; then CMD_ARGS+=(--pole-lon "$POLE_LON"); fi
if [ -n "$POLE_LAT" ]; then CMD_ARGS+=(--pole-lat "$POLE_LAT"); fi
if [ -n "$NX" ]; then CMD_ARGS+=(--nx "$NX"); fi
if [ -n "$NY" ]; then CMD_ARGS+=(--ny "$NY"); fi
if [ -n "$CUSTOM_GRID" ]; then CMD_ARGS+=(--custom-grid "$CUSTOM_GRID"); fi
if [ "$GLOBAL_CLOSURE" -eq 1 ]; then CMD_ARGS+=(--global-closure); fi
if [ "$BOUNDARY_POINTS" -eq 1 ]; then CMD_ARGS+=(--boundary-points); fi
if [ -n "$CUT_OFF" ]; then CMD_ARGS+=(--cut-off "$CUT_OFF"); fi
if [ -n "$LAKE_MIN_POINTS" ]; then CMD_ARGS+=(--lake-min-points "$LAKE_MIN_POINTS"); fi
if [ -n "$LAKE_MIN_FRACTION" ]; then CMD_ARGS+=(--lake-min-fraction "$LAKE_MIN_FRACTION"); fi
if [ "$LEGACY" -eq 1 ]; then CMD_ARGS+=(--legacy); fi
if [ "$LOCAL_POLYGONS" -eq 1 ]; then CMD_ARGS+=(--local-polygons); fi
if [ "$NO_USER_POLYGONS" -eq 1 ]; then CMD_ARGS+=(--no-user-polygons); fi
if [ "$ALL_POLYGONS" -eq 1 ]; then CMD_ARGS+=(--all-polygons); fi
if [ -n "$USER_POLYGONS_FLAG" ]; then CMD_ARGS+=(--user-polygons-flag "$USER_POLYGONS_FLAG"); fi

python3 -m gridgen.cli "${CMD_ARGS[@]}"

echo ""
echo "Execution finished successfully."
