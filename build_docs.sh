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
# @date Initial: 2026-10-13
# @date Latest Update: 2026-10-13

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

CLEANUP=0

usage() {
  cat << 'EOF'
Usage: ./build_docs.sh [OPTIONS]

Generate or clean Doxygen documentation for the WAVEWATCH III / IV Gridgen package.

Options:
  -c, --clean, --cleanup  Remove generated documentation output directory (docs/)
  -h, --help              Display this usage message and exit
EOF
}

# Parse Arguments
while [[ $# -gt 0 ]]; do
  case "$1" in
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

if [ "$CLEANUP" -eq 1 ]; then
  echo "Cleaning up generated documentation directory (docs/)..."
  if [ -d "docs" ]; then
    rm -rf docs
    echo "Removed docs/ directory."
  else
    echo "No docs/ directory found. Nothing to clean."
  fi
  exit 0
fi

if ! command -v doxygen &> /dev/null; then
    echo "Error: doxygen command not found. Please install Doxygen." >&2
    exit 1
fi

echo "Generating Doxygen documentation..."
doxygen Doxyfile

echo "Documentation generated successfully at docs/html/index.html"
