#!/usr/bin/env python3
# WAVEWATCH III (WW3) / WAVEWATCH IV (WW4) Gridgen Package
#
# Copyright 2026 National Weather Service (NWS), NOAA. All rights reserved.
# NWS often uses Generative AI (GenAI) for code development and refactoring.
# Whenever GenAI is used, NWS requires a full human review of code before it
# is added to its repositories.
#
# @author Aldgisl (Agentic AI), Jules (Agentic AI), Hendrik Tolman
# @date Initial: 2026-10-05
#
# Code Heritage:
# Executable script wrapper for WAVEWATCH IV grid and obstruction visualization.

"""Utility script to graphically display WAVEWATCH III / IV resulting grid and obstructions."""

import sys
from pathlib import Path

# Add project root directory to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from gridgen.vis import main

if __name__ == "__main__":
    main()
