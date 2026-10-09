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
# @date Latest Update: 2026-10-09

"""Unit tests for grid coordinate generation routines."""

from __future__ import annotations

import numpy as np
import pytest
from scipy.io import savemat

from gridgen.coordinates import (
    create_grid_coordinates,
    create_regular_grid,
    create_rotated_pole_grid,
    create_stereographic_grid,
    load_custom_grid,
)


def test_create_regular_grid() -> None:
    """Test regular 2D lon-lat grid generation with mandatory corner bounds and optional rotated pole."""
    # 1. Standard regular grid (unrotated)
    lon, lat = create_regular_grid(
        LON_START=100.0,
        LON_END=110.0,
        LAT_START=20.0,
        LAT_END=30.0,
        NX=6,
        NY=6,
    )

    assert lon.shape == (6, 6)
    assert lat.shape == (6, 6)
    assert np.isclose(lon[0, 0], 100.0)
    assert np.isclose(lon[0, -1], 110.0)
    assert np.isclose(lat[0, 0], 20.0)
    assert np.isclose(lat[-1, 0], 30.0)

    # 2. Rotated pole specified (lat != 90)
    rlon, rlat = create_regular_grid(
        LON_START=-10.0,
        LON_END=10.0,
        LAT_START=-10.0,
        LAT_END=10.0,
        NX=15,
        NY=15,
        POLE_LON=180.0,
        POLE_LAT=60.0,
    )
    assert rlon.shape == (15, 15)
    assert rlat.shape == (15, 15)
    assert np.all(rlon >= 0.0) and np.all(rlon < 360.0)

    # 3. Pole at North Pole (lat = 90.0) reverts to standard unrotated regular grid
    lon_np, lat_np = create_regular_grid(
        LON_START=100.0,
        LON_END=110.0,
        LAT_START=20.0,
        LAT_END=30.0,
        NX=6,
        NY=6,
        POLE_LON=0.0,
        POLE_LAT=90.0,
    )
    assert np.allclose(lon_np, lon)
    assert np.allclose(lat_np, lat)


def test_grid_parameter_defaults_and_validation_errors() -> None:
    """Test default values and parameter validation error messages for required grid inputs."""
    # 1. Regular grid with default parameters (lon: 140-240, lat: 44-75, nx: 401, ny: 125)
    lon, lat = create_grid_coordinates("regular")
    assert lon.shape == (125, 401)
    assert lat.shape == (125, 401)
    assert np.isclose(lon[0, 0], 140.0)
    assert np.isclose(lon[0, -1], 240.0)
    assert np.isclose(lat[0, 0], 44.0)
    assert np.isclose(lat[-1, 0], 75.0)

    # 2. Missing custom_grid path for custom grid type
    with pytest.raises(ValueError, match="Missing mandatory parameter '--custom-grid'"):
        create_grid_coordinates("custom")

    # 3. Missing CENTER_LON/CENTER_LAT for stereographic grid
    with pytest.raises(
        ValueError, match=r"Missing mandatory parameter\(s\) for stereographic grid: --center-lon, --center-lat"
    ):
        create_grid_coordinates("stereographic")

    # 4. Missing stereographic extent parameter
    with pytest.raises(
        ValueError, match=r"Missing mandatory parameter\(s\) for stereographic grid: --extent-km or --extent-deg"
    ):
        create_grid_coordinates("stereographic", CENTER_LON=0.0, CENTER_LAT=90.0)


def test_create_stereographic_grid() -> None:
    """Test general stereographic grid generation using km and arc degree options over discrete dimensions."""
    # 1. Polar center with km option
    lon1, lat1 = create_stereographic_grid(
        CENTER_LON=0.0,
        CENTER_LAT=90.0,
        EXTENT_KM=500.0,
        NX=11,
        NY=11,
    )
    assert lon1.shape == (11, 11)
    assert lat1.shape == (11, 11)
    cy, cx = lon1.shape[0] // 2, lon1.shape[1] // 2
    assert np.isclose(lat1[cy, cx], 90.0, atol=1e-3)

    # 2. Polar center with arc degree option
    lon_deg, lat_deg = create_stereographic_grid(
        CENTER_LON=0.0,
        CENTER_LAT=90.0,
        EXTENT_DEG=4.4966,  # ~500 km
        NX=11,
        NY=11,
    )
    assert lon_deg.shape == lon1.shape
    assert lat_deg.shape == lat1.shape
    assert np.isclose(lat_deg[cy, cx], 90.0, atol=1e-3)

    # 3. Oblique center
    lon2, lat2 = create_stereographic_grid(
        CENTER_LON=-75.0,
        CENTER_LAT=40.0,
        EXTENT_KM=300.0,
        NX=13,
        NY=13,
    )
    cy2, cx2 = lon2.shape[0] // 2, lon2.shape[1] // 2
    assert np.isclose(lat2[cy2, cx2], 40.0, atol=1e-3)
    assert np.isclose(lon2[cy2, cx2], 285.0, atol=1e-3)  # -75 mod 360 = 285

    # 4. Rotated stereographic center
    lon_rot, lat_rot = create_stereographic_grid(
        CENTER_LON=0.0,
        CENTER_LAT=90.0,
        EXTENT_KM=500.0,
        NX=11,
        NY=11,
        ROTATION=45.0,
    )
    assert lon_rot.shape == (11, 11)
    assert lat_rot.shape == (11, 11)
    assert np.isclose(lat_rot[cy, cx], 90.0, atol=1e-3)


def test_create_rotated_pole_grid() -> None:
    """Test rotated pole spherical grid helper routine."""
    lon, lat = create_rotated_pole_grid(
        LON_START=-10.0,
        LON_END=10.0,
        LAT_START=-10.0,
        LAT_END=10.0,
        POLE_LON=180.0,
        POLE_LAT=60.0,
        NX=15,
        NY=15,
    )

    assert lon.shape == (15, 15)
    assert lat.shape == (15, 15)
    assert np.all(lon >= 0.0) and np.all(lon < 360.0)
    assert np.all(lat >= -90.0) and np.all(lat <= 90.0)


def test_create_grid_coordinates_unified() -> None:
    """Test unified entry point create_grid_coordinates."""
    # 1. Regular unrotated
    lon1, lat1 = create_grid_coordinates(
        "regular", LON_START=0, LON_END=10, LAT_START=0, LAT_END=10, NX=11, NY=11
    )
    assert lon1.shape == (11, 11)
    assert lat1.shape == (11, 11)

    # 2. Regular rotated pole
    lon_rot, lat_rot = create_grid_coordinates(
        "regular",
        LON_START=-10,
        LON_END=10,
        LAT_START=-10,
        LAT_END=10,
        NX=11,
        NY=11,
        POLE_LON=180.0,
        POLE_LAT=60.0,
    )
    assert lon_rot.shape == (11, 11)
    assert lat_rot.shape == (11, 11)

    # 3. General Stereographic in km
    lon2, lat2 = create_grid_coordinates(
        "stereographic", CENTER_LON=0.0, CENTER_LAT=90.0, EXTENT_KM=200, NX=11, NY=11
    )
    assert lon2.shape == (11, 11)
    assert lat2.shape == (11, 11)

    # 4. General Stereographic in arc degrees
    lon3, lat3 = create_grid_coordinates(
        "stereographic", CENTER_LON=0.0, CENTER_LAT=90.0, EXTENT_DEG=2.0, NX=11, NY=11
    )
    assert lon3.shape == (11, 11)
    assert lat3.shape == (11, 11)

    # 4. Invalid type
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
