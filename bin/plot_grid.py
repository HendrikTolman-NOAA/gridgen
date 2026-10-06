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
# @date Update: 2026-10-06
#
# Code Heritage:
# Executable script wrapper for WAVEWATCH IV grid and obstruction visualization.

"""Utility script to graphically display WAVEWATCH III / IV resulting grid and obstructions."""

import os
import sys
from pathlib import Path

# Add project root directory to sys.path and set working directory to repo root
repo_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(repo_root))

orig_pwd = Path.cwd()

# Resolve relative input/output arguments relative to original invocation directory
for idx, arg in enumerate(sys.argv):
    if arg in ("-i", "--input") and idx + 1 < len(sys.argv):
        inp = Path(sys.argv[idx + 1])
        if not inp.is_absolute():
            sys.argv[idx + 1] = str((orig_pwd / inp).resolve())
    elif arg in ("-o", "--output") and idx + 1 < len(sys.argv):
        outp = Path(sys.argv[idx + 1])
        if not outp.is_absolute():
            sys.argv[idx + 1] = str((orig_pwd / outp).resolve())

os.chdir(repo_root)

from gridgen.vis import main

if __name__ == "__main__":
    main()
