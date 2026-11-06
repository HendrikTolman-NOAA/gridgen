#!/usr/bin/env bash
# WAVEWATCH III (WW3) / WAVEWATCH IV (WW4) Gridgen Package
#
# Copyright 2026 National Weather Service (NWS), NOAA. All rights reserved.
# NWS often uses Generative AI (GenAI) for code development and refactoring.
# Whenever GenAI is used, NWS requires a full human review of code before it
# is added to its repositories.
#
# @author Hendrik Tolman
# @date Initial: 2026-11-06
# @date Latest Update: 2026-11-06
#
# @brief Example driver script for WAVEWATCH III / IV grid generation.
# @details This script can be run directly to create a set of predefined grids,
#          or individual commands can be copied from this file to be run
#          interactively in a terminal (replacing shell script variables)

set -euo pipefail

# Configuration: Bathy source, accuracy level of coastal polygons and output file directory
BATHY_SOURCE="gebco_2024"
COASTAL_BOUND="full"
OUT_DIR="gridgen_grids"

# Ensure target output directory exists
mkdir -p "${OUT_DIR}"

# ---------------------------------------------------------------------------

# Gulf and Caribbean on regular grid

  run_gridgen.sh -n Gulf_Caribbean_regular -o $OUT_DIR --nx 361 --lon-start -100 --lon-end -55. --ny 201 --lat-start 7. --lat-end 32. --bathy-source $BATHY_SOURCE --bound-file $COASTAL_BOUND --active-file Gulf_and_Caribbean.active --boundary-points

# Gulf and Caribbean on regular grid with pole rotation in mapping 

  run_gridgen.sh -n Gulf_Caribbean_rotated -o $OUT_DIR --nx 541 --lon-start -100 --lon-end -55. --ny 301 --lat-start 7. --lat-end 32. --bathy-source $BATHY_SOURCE --bound-file $COASTAL_BOUND --active-file Gulf_and_Caribbean.active --boundary-points --pole-lon 102.5 --pole-lat 80.5

# Gulf and Caribbean on stereographic grid

  run_gridgen.sh --grid-type stereographic -o $OUT_DIR --nx 601 --ny 401 --center-lon -77. --center-lat 20.7  --extent-deg 14.35 --bathy-source $BATHY_SOURCE --bound-file $COASTAL_BOUND --active-file Gulf_and_Caribbean.active --boundary-points

# Alaska regional regular grid with pole rotation 

  run_gridgen.sh -n Alaska_regular -o $OUT_DIR --nx 401 --lon-start 140. --lon-end 240.. --ny 125 --lat-start 44. --lat-end 75. --bathy-source $BATHY_SOURCE --bound-file $COASTAL_BOUND  --boundary-points 140. 240. 44. 65.

# Arctic stereographic

  run_gridgen.sh -n Arctic_stereo -o $OUT_DIR -g stereographic --nx 401 --ny 401 --center-lat 90. --center-lon 0. --extent-deg 30. --rotation -45. --bathy-source $BATHY_SOURCE --bound-file $COASTAL_BOUND --boundary-points --active-file Arctic.active

# Antarctic stereographic

  run_gridgen.sh -n Antarctic_stereo -o $OUT_DIR -g stereographic --nx 401 --ny 401 --center-lat -90. --center-lon 0. --extent-deg 30. --rotation 30. --bathy-source $BATHY_SOURCE --bound-file $COASTAL_BOUND

# ---------------------------------------------------------------------------

