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
# @date Latest Update: 2026-10-07

"""Unit tests for grid coordinate generation routines."""

from __future__ import annotations

import numpy as np
import pytest
from scipy.io import savemat

from gridgen.coordinates import (
    create_grid_coordinates,
    create_lambert_conformal_grid,
    create_regular_grid,
    create_rotated_pole_grid,
    create_stereographic_grid,
    load_custom_grid,
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

    # 5. Custom Grid
    # Tested via custom_grid file loading tests below

    # 6. Invalid type
    with pytest.raises(ValueError, match="Unsupported grid_type"):
        create_grid_coordinates("mercator")


def test_load_custom_grid_netcdf(tmp_path) -> None:
    """Test loading custom grid coordinates from NetCDF file."""
    import netCDF4 as nc

    nc_file = tmp_path / "custom_grid.nc"
    lon_in = np.array([[10.0, 11.0], [10.0, 11.0]])
    lat_in = np.array([[20.0, 20.0], [21.0, 21.0]])

    with nc.Dataset(nc_file, "w") as ds:
        ds.createDimension("y", 2)
        ds.createDimension("x", 2)
        vlon = ds.createVariable("longitude", "f8", ("y", "x"))
        vlat = ds.createVariable("latitude", "f8", ("y", "x"))
        vlon[:] = lon_in
        vlat[:] = lat_in

    lon_out, lat_out = load_custom_grid(nc_file)
    assert np.allclose(lon_out, lon_in)
    assert np.allclose(lat_out, lat_in)


def test_load_custom_grid_npz(tmp_path) -> None:
    """Test loading custom grid coordinates from NPZ archive."""
    npz_file = tmp_path / "custom_grid.npz"
    lon_in, lat_in = np.meshgrid(np.linspace(140, 150, 5), np.linspace(40, 50, 5))
    np.savez(npz_file, lon=lon_in, lat=lat_in)

    lon_out, lat_out = load_custom_grid(npz_file)
    assert np.allclose(lon_out, lon_in)
    assert np.allclose(lat_out, lat_in)


def test_load_custom_grid_mat(tmp_path) -> None:
    """Test loading custom grid coordinates from MAT file."""
    mat_file = tmp_path / "custom_grid.mat"
    lon_in, lat_in = np.meshgrid(np.linspace(10, 20, 4), np.linspace(30, 40, 4))
    savemat(mat_file, {"lon": lon_in, "lat": lat_in})

    lon_out, lat_out = load_custom_grid(mat_file)
    assert np.allclose(lon_out, lon_in)
    assert np.allclose(lat_out, lat_in)


def test_load_custom_grid_csv(tmp_path) -> None:
    """Test loading custom grid coordinates from CSV file."""
    csv_file = tmp_path / "custom_grid.csv"
    data = np.array([[10.0, 20.0], [11.0, 21.0], [12.0, 22.0]])
    np.savetxt(csv_file, data, delimiter=",")

    lon_out, lat_out = load_custom_grid(csv_file)
    assert lon_out.shape == (3, 3)
    assert lat_out.shape == (3, 3)


def test_load_custom_grid_errors(tmp_path) -> None:
    """Test error handling in load_custom_grid for invalid or missing files."""
    # 1. Missing file
    with pytest.raises(FileNotFoundError, match="Custom grid file not found"):
        load_custom_grid(tmp_path / "non_existent.nc")

    # 2. Unsupported extension
    dummy_file = tmp_path / "grid.unknown"
    dummy_file.write_text("hello")
    with pytest.raises(ValueError, match="Unsupported custom grid file format"):
        load_custom_grid(dummy_file)


def test_create_grid_coordinates_custom(tmp_path) -> None:
    """Test create_grid_coordinates with grid_type='custom' and custom_grid path."""
    npz_file = tmp_path / "my_custom_grid.npz"
    lon_in, lat_in = np.meshgrid(np.linspace(100, 110, 3), np.linspace(10, 20, 3))
    np.savez(npz_file, lon=lon_in, lat=lat_in)

    lon_out, lat_out = create_grid_coordinates("custom", custom_grid=str(npz_file))
    assert lon_out.shape == (3, 3)
    assert lat_out.shape == (3, 3)
    assert np.allclose(lon_out, lon_in)
