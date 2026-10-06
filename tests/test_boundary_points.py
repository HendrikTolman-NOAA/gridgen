# WAVEWATCH III (WW3) / WAVEWATCH IV (WW4) Gridgen Package
#
# Copyright 2026 National Weather Service (NWS), NOAA. All rights reserved.
# NWS often uses Generative AI (GenAI) for code development and refactoring.
# Whenever GenAI is used, NWS requires a full human review of code before it
# is added to its repositories.
#
# @author Aldgisl (Agentic AI), Hendrik Tolman
# @author Jules (Agentic AI) (contributor)
# @date Initial: 2026-10-06
# @date Latest Update: 2026-10-06

"""Unit tests for defining input boundary points in regional grids."""

from __future__ import annotations

import numpy as np

from gridgen.coordinates import create_regular_grid
from gridgen.masking import define_boundary_points, modify_mask


def test_define_boundary_points_edges() -> None:
    """Test setting outer domain boundary wet cells to mask value 2."""
    lon, lat = create_regular_grid(lon_start=0, lon_end=4, lat_start=0, lat_end=4, dx=1, dy=1)
    mask = np.ones((5, 5), dtype=int)
    # Set one cell to dry land
    mask[0, 0] = 0

    m_new = define_boundary_points(mask, lon, lat)

    # Dry land remains 0
    assert m_new[0, 0] == 0
    # Outer wet cells set to 2
    assert m_new[0, 1] == 2
    assert m_new[4, 4] == 2
    # Inner wet cells remain 1
    assert m_new[2, 2] == 1


def test_define_boundary_points_active_poly() -> None:
    """Test defining active computation polygon region and internal boundaries."""
    lon, lat = create_regular_grid(lon_start=0, lon_end=10, lat_start=0, lat_end=10, dx=1, dy=1)
    mask = np.ones((11, 11), dtype=int)

    # Active polygon covering center (2,2) to (8,8)
    px = np.array([2.0, 8.0, 8.0, 2.0, 2.0])
    py = np.array([2.0, 2.0, 8.0, 8.0, 2.0])

    m_new = define_boundary_points(mask, lon, lat, active_poly=(px, py))

    # Center cell is active wet (1)
    assert m_new[5, 5] == 1
    # Outside cell (0, 0) is inactive (3)
    assert m_new[0, 0] == 3


def test_modify_mask_alias() -> None:
    """Test modify_mask backward compatibility alias."""
    lon, lat = create_regular_grid(lon_start=0, lon_end=4, lat_start=0, lat_end=4, dx=1, dy=1)
    mask = np.ones((5, 5), dtype=int)

    m_new = modify_mask(mask, lon, lat)
    assert m_new[0, 1] == 2
