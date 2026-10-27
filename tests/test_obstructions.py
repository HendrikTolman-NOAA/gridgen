# WAVEWATCH III (WW3) / WAVEWATCH IV (WW4) Gridgen Package
#
# Copyright 2026 National Weather Service (NWS), NOAA. All rights reserved.
# NWS often uses Generative AI (GenAI) for code development and refactoring.
# Whenever GenAI is used, NWS requires a full human review of code before it
# is added to its repositories.
#
# @author Aldgisl (Agentic AI), Hendrik Tolman
# @author Jules (Agentic AI) (contributor)
# @date Initial: 2026-10-27
# @date Latest Update: 2026-10-27

"""Unit tests for subgrid obstruction calculations (gridgen/obstructions.py)."""

from __future__ import annotations

import numpy as np

from gridgen.masking import load_mat_polygons
from gridgen.obstructions import create_obstr


def test_create_obstr_empty_bounds():
    """Verify that create_obstr returns zero arrays when bound_list is empty."""
    x, y = np.meshgrid(np.linspace(0, 10, 5), np.linspace(0, 10, 5))
    mask = np.ones_like(x, dtype=int)
    ObsX, ObsY = create_obstr(x, y, [], mask)

    assert ObsX.shape == x.shape
    assert ObsY.shape == y.shape
    assert np.all(ObsX == 0.0)
    assert np.all(ObsY == 0.0)


def test_create_obstr_mat_array_shape_and_periodicity():
    """Verify that create_obstr handles 2D column vector shapes from MAT files and periodic longitudes."""
    # Define a test grid in [-160, -150] longitude (Pacific/Hawaii region)
    lon1d = np.linspace(-160, -150, 10)
    lat1d = np.linspace(18, 22, 10)
    lon, lat = np.meshgrid(lon1d, lat1d)
    mask = np.ones_like(lon, dtype=int)

    # Polygon in [200, 205] longitude (0 to 360 convention as found in coastal_bound_*.mat)
    # shaped as (N, 1) column vectors as returned by scipy.io.loadmat
    poly_bx = np.array([201.0, 204.0, 204.0, 201.0, 201.0], dtype=np.float64).reshape(-1, 1)
    poly_by = np.array([19.0, 19.0, 21.0, 21.0, 19.0], dtype=np.float64).reshape(-1, 1)

    bound_list = [
        {
            "x": poly_bx,
            "y": poly_by,
            "level": np.array([[1]]),
        }
    ]

    ObsX, ObsY = create_obstr(lon, lat, bound_list, mask)

    assert ObsX.shape == lon.shape
    assert ObsY.shape == lon.shape
    assert np.max(ObsX) > 0.0
    assert np.max(ObsY) > 0.0


def test_create_obstr_caribbean_region():
    """Verify that create_obstr calculates obstructions for islands in the Caribbean [-80, -60] lon."""
    lon1d = np.linspace(-75, -65, 10)
    lat1d = np.linspace(15, 20, 10)
    lon, lat = np.meshgrid(lon1d, lat1d)
    mask = np.ones_like(lon, dtype=int)

    # Island polygon in [-72, -68] lon (or [288, 292] lon in 0..360)
    poly_bx = np.array([-72.0, -68.0, -68.0, -72.0, -72.0])
    poly_by = np.array([16.0, 16.0, 19.0, 19.0, 16.0])

    bound_list = [{"x": poly_bx, "y": poly_by, "level": 2}]

    ObsX, ObsY = create_obstr(lon, lat, bound_list, mask)

    assert np.max(ObsX) > 0.0
    assert np.max(ObsY) > 0.0


def test_create_obstr_multiple_intersecting_polygons():
    """Verify that create_obstr accurately calculates combined obstructions across multiple overlapping/intersecting polygons."""
    lon1d = np.array([0.0, 1.0])
    lat1d = np.array([0.0, 1.0])
    lon, lat = np.meshgrid(lon1d, lat1d)
    mask = np.ones_like(lon, dtype=int)

    # Two overlapping polygons inside cell [0,0] (span: [0, 1] x [0, 1])
    poly1_x = np.array([0.1, 0.4, 0.4, 0.1, 0.1])
    poly1_y = np.array([0.1, 0.1, 0.4, 0.4, 0.1])

    poly2_x = np.array([0.3, 0.6, 0.6, 0.3, 0.3])
    poly2_y = np.array([0.1, 0.1, 0.4, 0.4, 0.1])

    bound_list = [
        {"x": poly1_x, "y": poly1_y, "level": 1},
        {"x": poly2_x, "y": poly2_y, "level": 1},
    ]

    ObsX, ObsY = create_obstr(lon, lat, bound_list, mask)

    # Combined union inside cell [0,0] (x-bounds [-0.5, 0.5], y-bounds [-0.5, 0.5]):
    # x-span is [0.1, 0.5] (width = 0.4 -> ObsY = 0.4) and y-span is [0.1, 0.4] (height = 0.3 -> ObsX = 0.3)
    assert np.isclose(ObsX[0, 0], 0.3)
    assert np.isclose(ObsY[0, 0], 0.4)


def test_load_mat_polygons_nonexistent():
    """Verify load_mat_polygons returns an empty list for nonexistent file paths."""
    polys = load_mat_polygons("nonexistent_file.mat")
    assert polys == []
