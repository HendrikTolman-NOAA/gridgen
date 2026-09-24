#!/usr/bin/env bash
# WAVEWATCH III (WW3) / WAVEWATCH IV (WW4) Gridgen Package
#
# Copyright 2026 National Weather Service (NWS), NOAA. All rights reserved.
# NWS often uses Generative AI (GenAI) for code development and refactoring.
# Whenever GenAI is used, NWS requires a full human review of code before it
# is added to its repositories.
#
# @author Aldgisl (Agentic AI), Jules (Agentic AI), Hendrik Tolman
# @date Initial: 2026-09-24
#
# Utility tool to populate the reference_data directory with authoritative
# bathymetry, shoreline, and regional polygon datasets required by WAVEWATCH.

set -euo pipefail

# Default Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TARGET_DIR="${SCRIPT_DIR}/reference_data"

# URLs for authoritative data sources
NCEP_GRIDGEN_URL="ftp://polar.ncep.noaa.gov/waves/gridgen/gridgen_addit.tar.gz"
ETOPO2022_60S_TIF_URL="https://www.ngdc.noaa.gov/mgg/global/relief/ETOPO2022/data/60s/60s_bed_elev_gtif/ETOPO_2022_v1_60s_N90W180_bed.tif"
ETOPO2022_30S_TIF_URL="https://www.ngdc.noaa.gov/mgg/global/relief/ETOPO2022/data/30s/30s_bed_elev_gtif/ETOPO_2022_v1_30s_N90W180_bed.tif"

# Flags
FETCH_LEGACY=false
FETCH_ETOPO2022=false
FETCH_GEBCO=false
FETCH_GSHHG=false
CLI_SPECIFIED=false

usage() {
  cat << 'EOF'
Usage: ./populate_reference_data.sh [OPTIONS]

Tool to populate the WAVEWATCH gridgen reference_data directory from authoritative sources.

Options:
  -d, --target-dir DIR   Specify target output directory (default: ./reference_data)
  --legacy               Pull legacy reference datasets (etopo1.nc, etopo2.nc, coastal_bound_*.mat)
  --etopo2022            Pull newer NOAA NCEI ETOPO 2022 global relief model dataset
  --gebco                Display instructions & links for GEBCO global bathymetry grid
  --gshhg                Display instructions & links for GSHHG v2.3.7 vector shoreline database
  --all                  Pull all available external datasets (legacy + newer ETOPO 2022)
  -h, --help             Display this help message and exit

Default Behavior:
  When run with no dataset options, the script pulls and extracts all needed and
  optional legacy reference data (gridgen_addit.tar.gz from NCEP FTP) into target directory,
  and prints suggestions for newer authoritative datasets.

Authoritative External Data Sources:
  1. Legacy NCEP Gridgen:
     ftp://polar.ncep.noaa.gov/waves/gridgen/gridgen_addit.tar.gz
     Provides: etopo1.nc, etopo2.nc, coastal_bound_*.mat, optional_coastal_polygons.mat
  2. ETOPO 2022 (NOAA NCEI):
     https://www.ngdc.noaa.gov/mgg/global/relief/ETOPO2022/data/
     Replaces ETOPO1/2 with higher resolution 15s/30s/60s global bathymetry & topography.
  3. GEBCO (IHO/IOC):
     https://www.gebco.net/data_and_products/gridded_bathymetry_data/
     15 arc-second global grid of ocean bathymetry.
  4. GSHHG v2.3.7 (NOAA/SOEST):
     https://www.ngdc.noaa.gov/mgg/shorelines/
     Global Self-consistent, Hierarchical, High-resolution Geography database.
EOF
}

# Parse Arguments
while [[ $# -gt 0 ]]; do
  case "$1" in
    -d|--target-dir)
      TARGET_DIR="$2"
      shift 2
      ;;
    --legacy)
      FETCH_LEGACY=true
      CLI_SPECIFIED=true
      shift
      ;;
    --etopo2022)
      FETCH_ETOPO2022=true
      CLI_SPECIFIED=true
      shift
      ;;
    --gebco)
      FETCH_GEBCO=true
      CLI_SPECIFIED=true
      shift
      ;;
    --gshhg)
      FETCH_GSHHG=true
      CLI_SPECIFIED=true
      shift
      ;;
    --all)
      FETCH_LEGACY=true
      FETCH_ETOPO2022=true
      FETCH_GEBCO=true
      FETCH_GSHHG=true
      CLI_SPECIFIED=true
      shift
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

# Default to legacy dataset if no specific dataset flag was requested
if [ "$CLI_SPECIFIED" = false ]; then
  FETCH_LEGACY=true
fi

# Ensure target directory exists
mkdir -p "$TARGET_DIR"

# Download Tool Selection
DOWNLOAD_CMD=""
if command -v curl &> /dev/null; then
  DOWNLOAD_CMD="curl"
elif command -v wget &> /dev/null; then
  DOWNLOAD_CMD="wget"
else
  echo "Error: Neither 'curl' nor 'wget' was found on your system. Please install one to proceed." >&2
  exit 1
fi

download_file() {
  local url="$1"
  local dest="$2"
  echo "Downloading ${url} -> ${dest}..."
  if [ "$DOWNLOAD_CMD" = "curl" ]; then
    curl -L -f --progress-bar -o "$dest" "$url"
  else
    wget -O "$dest" "$url"
  fi
}

echo "========================================================================"
echo " WAVEWATCH III / IV Reference Data Population Tool"
echo " Target Directory: ${TARGET_DIR}"
echo "========================================================================"

# 1. Fetch Legacy Data
if [ "$FETCH_LEGACY" = true ]; then
  echo ""
  echo "--> Processing Present / Legacy Datasets (NOAA NCEP Distribution)..."
  TARBALL="${TARGET_DIR}/gridgen_addit.tar.gz"

  # Download archive if needed files are not already present
  if [ ! -f "${TARGET_DIR}/etopo1.nc" ] || [ ! -f "${TARGET_DIR}/coastal_bound_full.mat" ]; then
    download_file "$NCEP_GRIDGEN_URL" "$TARBALL"
    echo "Extracting ${TARBALL} into ${TARGET_DIR}..."
    tar -xvf "$TARBALL" -C "$TARGET_DIR"
    rm -f "$TARBALL"
    echo "Legacy dataset extraction complete."
  else
    echo "Legacy reference data files (etopo1.nc, coastal_bound_*.mat) already present in ${TARGET_DIR}."
  fi
fi

# 2. Fetch ETOPO 2022
if [ "$FETCH_ETOPO2022" = true ]; then
  echo ""
  echo "--> Processing ETOPO 2022 Global Relief Model (NOAA NCEI)..."
  ETOPO_DEST="${TARGET_DIR}/ETOPO_2022_v1_60s_N90W180_bed.tif"
  if [ ! -f "$ETOPO_DEST" ]; then
    download_file "$ETOPO2022_60S_TIF_URL" "$ETOPO_DEST"
    echo "Downloaded ETOPO 2022 (60s bed elevation GeoTIFF)."
  else
    echo "ETOPO 2022 dataset already present at ${ETOPO_DEST}."
  fi
fi

# 3. Suggest GEBCO Data Source
if [ "$FETCH_GEBCO" = true ] || [ "$CLI_SPECIFIED" = false ]; then
  echo ""
  echo "========================================================================"
  echo " SUGGESTION: Newer Authoritative Bathymetry Source - GEBCO 2024"
  echo "========================================================================"
  echo " The General Bathymetric Chart of the Oceans (GEBCO) provides a global"
  echo " 15 arc-second bathymetry grid (GEBCO_2024 NetCDF format)."
  echo " You can obtain GEBCO bathymetry directly from:"
  echo "   https://www.gebco.net/data_and_products/gridded_bathymetry_data/"
fi

# 4. Suggest GSHHG Shoreline Data Source
if [ "$FETCH_GSHHG" = true ] || [ "$CLI_SPECIFIED" = false ]; then
  echo ""
  echo "========================================================================"
  echo " SUGGESTION: Newer Authoritative Shoreline Source - GSHHG v2.3.7"
  echo "========================================================================"
  echo " GSHHG v2.3.7 is the latest release of the Global Self-consistent,"
  echo " Hierarchical, High-resolution Geography database."
  echo " Shapefiles and NetCDF vectors can be obtained directly from:"
  echo "   https://www.ngdc.noaa.gov/mgg/shorelines/"
fi

echo ""
echo "Reference data population task finished successfully."
