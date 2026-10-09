# WAVEWATCH III (WW3) / WAVEWATCH IV (WW4) Gridgen Package
#
# Copyright 2026 National Weather Service (NWS), NOAA. All rights reserved.
# NWS often uses Generative AI (GenAI) for code development and refactoring.
# Whenever GenAI is used, NWS requires a full human review of code before it
# is added to its repositories.
#
# @author Aldgisl (Agentic AI), Hendrik Tolman
# @author Jules (Agentic AI) (contributor)
# @date Initial: 2026-09-22
# @date Latest Update: 2026-10-08
#
# Code Heritage:
# Converted from MATLAB gridgen suite originally authored by NCEP/NOAA
# (Arun Chawla, Stylianos Flampouris, Deanna Spindler).

"""WAVEWATCH III (WW3) / WAVEWATCH IV (WW4) Gridgen Package."""

from __future__ import annotations

from .coordinates import (
    create_grid_coordinates,
    create_regular_grid,
    create_rotated_pole_grid,
    create_stereographic_grid,
)
from .masking import (
    clean_mask,
    compute_boundary,
    define_boundary_points,
    load_user_polygons,
    modify_mask,
    remove_lake,
    split_boundary,
)

__version__ = "3.0.0"

__all__ = [
    "clean_mask",
    "compute_boundary",
    "create_grid_coordinates",
    "create_regular_grid",
    "create_rotated_pole_grid",
    "create_stereographic_grid",
    "define_boundary_points",
    "load_user_polygons",
    "modify_mask",
    "remove_lake",
    "split_boundary",
]
