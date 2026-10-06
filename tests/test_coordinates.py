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

"""Unit tests for grid coordinate generation routines."""

from __future__ import annotations

import numpy as np
import pytest

from gridgen.coordinates import (
    create_grid_coordinates,
    create_lambert_conformal_grid,
    create_regular_grid,
    create_rotated_pole_grid,
    create_stereographic_grid,
)


def test_create_regular_grid() -> None:
    """Test regular 2D lon-lat grid generation."""
    lon, lat = create_regular_grid(
        lon_start=100.0,
        lon_end=110.0,
        lat_start=20.0,
        lat_end=30.0,
        dx=2.0,
        dy=2.0,
    )

    assert lon.shape == (6, 6)
    assert lat.shape == (6, 6)
    assert np.isclose(lon[0, 0], 100.0)
    assert np.isclose(lon[0, -1], 110.0)
    assert np.isclose(lat[0, 0], 20.0)
    assert np.isclose(lat[-1, 0], 30.0)


def test_create_stereographic_grid() -> None:
    """Test general stereographic grid generation for oblique and polar centers."""
    # 1. Polar center
    lon1, lat1 = create_stereographic_grid(
        center_lon=0.0,
        center_lat=90.0,
        extent_km=500.0,
        resolution_km=100.0,
    )
    assert lon1.ndim == 2
    assert lat1.ndim == 2
    cy, cx = lon1.shape[0] // 2, lon1.shape[1] // 2
    assert np.isclose(lat1[cy, cx], 90.0, atol=1e-3)

    # 2. Oblique center
    lon2, lat2 = create_stereographic_grid(
        center_lon=-75.0,
        center_lat=40.0,
        extent_km=300.0,
        resolution_km=50.0,
    )
    cy2, cx2 = lon2.shape[0] // 2, lon2.shape[1] // 2
    assert np.isclose(lat2[cy2, cx2], 40.0, atol=1e-3)
    assert np.isclose(lon2[cy2, cx2], 285.0, atol=1e-3)  # -75 mod 360 = 285


def test_create_lambert_conformal_grid() -> None:
    """Test Lambert Conformal Conic grid generation."""
    lon, lat = create_lambert_conformal_grid(
        center_lon=-95.0,
        center_lat=35.0,
        lat_1=30.0,
        lat_2=60.0,
        extent_km=500.0,
        resolution_km=100.0,
    )

    assert lon.ndim == 2
    assert lat.ndim == 2
    cy, cx = lon.shape[0] // 2, lon.shape[1] // 2
    assert np.isclose(lat[cy, cx], 35.0, atol=1e-3)
    assert np.isclose(lon[cy, cx], 265.0, atol=1e-3)  # -95 mod 360 = 265


def test_create_rotated_pole_grid() -> None:
    """Test rotated pole spherical grid generation."""
    lon, lat = create_rotated_pole_grid(
        lon_start=-10.0,
        lon_end=10.0,
        lat_start=-10.0,
        lat_end=10.0,
        pole_lon=180.0,
        pole_lat=60.0,
        nx=15,
        ny=15,
    )

    assert lon.shape == (15, 15)
    assert lat.shape == (15, 15)
    assert np.all(lon >= 0.0) and np.all(lon < 360.0)
    assert np.all(lat >= -90.0) and np.all(lat <= 90.0)


def test_create_grid_coordinates_unified() -> None:
    """Test unified entry point create_grid_coordinates."""
    # 1. Regular
    lon1, lat1 = create_grid_coordinates("regular", lon_start=0, lon_end=10, lat_start=0, lat_end=10, dx=1, dy=1)
    assert lon1.shape == (11, 11)
    assert lat1.shape == (11, 11)

    # 2. General Stereographic
    lon2, lat2 = create_grid_coordinates("stereographic", extent_km=200, resolution_km=50)
    assert lon2.ndim == 2
    assert lat2.ndim == 2

    # 3. Lambert Conformal
    lon3, lat3 = create_grid_coordinates("lambert_conformal", extent_km=200, resolution_km=50)
    assert lon3.ndim == 2
    assert lat3.ndim == 2

    # 4. Rotated Pole
    lon4, lat4 = create_grid_coordinates("rotated_pole", nx=10, ny=10)
    assert lon4.shape == (10, 10)
    assert lat4.shape == (10, 10)

    # 5. Invalid type
    with pytest.raises(ValueError, match="Unsupported grid_type"):
        create_grid_coordinates("mercator")
