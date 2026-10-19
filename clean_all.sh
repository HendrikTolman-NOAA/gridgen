#!/usr/bin/env bash
# WAVEWATCH III (WW3) / WAVEWATCH IV (WW4) Gridgen Package
#
# Copyright 2026 National Weather Service (NWS), NOAA. All rights reserved.
# NWS often uses Generative AI (GenAI) for code development and refactoring.
# Whenever GenAI is used, NWS requires a full human review of code before it
# is added to its repositories.
#
# @file clean_all.sh
# @brief Master cleanup script to remove all generated grid output, reference data, docs, and build cache artifacts.
# @author Aldgisl (Agentic AI), Hendrik Tolman
# @author Jules (Agentic AI) (contributor)
# @date Initial: 2026-10-15
# @date Latest Update: 2026-10-15
#
# Utility script to perform a comprehensive cleanup across the repository.

set -euo pipefail

ORIG_DIR="$(pwd)"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

usage() {
  cat << 'EOF'
Usage: ./clean_all.sh [OPTIONS]

Master cleanup utility script to remove all generated grid files, plot graphics,
reference datasets, documentation build outputs, and Python build/test cache artifacts.

Options:
  -h, --help             Display this help message and exit

Description:
  This script performs a full repository cleanup by:
    1. Removing generated grid output files (.depth_ascii, .maskorig_ascii, .obstr_lev1, .meta, _coards.nc, _ugrid.nc).
    2. Removing generated plot graphic images (.jpg, .jpeg, .png, .pdf, .eps, .gif).
    3. Cleaning reference data files in reference_data/ (via ./populate_reference_data.sh --clean).
    4. Removing generated documentation build directories (docs/html/, docs/latex/, etc. via ./docs/build_docs.sh --clean).
    5. Removing Python build, distribution, bytecode (__pycache__, *.pyc), and test cache artifacts (.pytest_cache, .ruff_cache, .coverage, build/, dist/, *.egg-info).
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
      echo "Error: Unknown option: $1" >&2
      usage
      exit 1
      ;;
  esac
done

echo "========================================================================"
echo " WAVEWATCH III / IV Gridgen Master Cleanup Utility"
echo "========================================================================"

# 1. Clean generated grid outputs and plot graphics in both current working directory and script root
echo "--> Cleaning generated grid output files and plot graphics..."
for target in "$ORIG_DIR" "$SCRIPT_DIR"; do
  if [ -d "$target" ]; then
    rm -f "${target}"/*.depth_ascii "${target}"/*.maskorig_ascii \
          "${target}"/*.obstr_lev1 "${target}"/*.meta \
          "${target}"/*_coards.nc "${target}"/*_ugrid.nc \
          "${target}"/*.jpg "${target}"/*.jpeg "${target}"/*.png \
          "${target}"/*.pdf "${target}"/*.eps "${target}"/*.gif
  fi
done

# 2. Clean reference data directory
if [ -f "${SCRIPT_DIR}/populate_reference_data.sh" ]; then
  echo "--> Cleaning reference data directory..."
  "${SCRIPT_DIR}/populate_reference_data.sh" --clean || true
fi

# 3. Clean documentation build outputs
if [ -f "${SCRIPT_DIR}/docs/build_docs.sh" ]; then
  echo "--> Cleaning documentation build outputs..."
  "${SCRIPT_DIR}/docs/build_docs.sh" --clean || true
fi

# 4. Clean Python build, test, and bytecode cache artifacts
echo "--> Cleaning Python build, test, and bytecode cache artifacts..."
for target in "$ORIG_DIR" "$SCRIPT_DIR"; do
  if [ -d "$target" ]; then
    rm -rf "${target}/build" "${target}/dist" "${target}"/*.egg-info \
           "${target}/.pytest_cache" "${target}/.ruff_cache" "${target}/.coverage" \
           "${target}/docs/html" "${target}/docs/latex" "${target}/docs/xml" \
           "${target}/docs/man" "${target}/docs/build"
    find "$target" -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
    find "$target" -type f -name "*.pyc" -delete 2>/dev/null || true
  fi
done

echo "========================================================================"
echo " Master cleanup finished successfully."
echo "========================================================================"
