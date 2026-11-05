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
# @date Latest Update: 2026-11-04

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
    geo_to_rotated_coords,
    load_custom_grid,
    rotated_to_geo_coords,
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
    """Test default values and parameter validation for grid inputs."""
    # 1. Regular grid works with default parameters when arguments are omitted
    lon_def, lat_def = create_grid_coordinates("regular")
    assert lon_def.shape == (601, 1440)
    assert lat_def.shape == (601, 1440)
    assert np.isclose(lon_def[0, 0], 0.0)
    assert np.isclose(lon_def[0, -1], 359.75)
    assert np.isclose(lat_def[0, 0], -90.0)
    assert np.isclose(lat_def[-1, 0], 90.0)

    # 1b. Regular grid with custom parameters
    lon, lat = create_grid_coordinates(
        "regular", LON_START=20.0, LAT_START=-75.0, LON_END=379.75, LAT_END=75.0
    )
    assert lon.shape == (601, 1440)
    assert lat.shape == (601, 1440)
    assert np.isclose(lon[0, 0], 20.0)
    assert np.isclose(lon[0, -1], 379.75)


def test_create_regular_grid_auto_global_closure_nx_sx() -> None:
    """Test that NX * SX == 360 automatically switches on global closure even if flag is False."""
    lon, lat = create_regular_grid(
        LON_START=0.0,
        LAT_START=-90.0,
        LAT_END=90.0,
        NX=360,
        SX=1.0,
        NY=181,
        global_closure=False,
    )
    assert lon.shape == (181, 360)
    assert np.isclose(lon[0, 0], 0.0)
    assert np.isclose(lon[0, -1], 359.0)
    assert np.isclose(lat[0, 0], -90.0)
    assert np.isclose(lat[-1, 0], 90.0)

    # 2. Missing custom_grid path for custom grid type
    with pytest.raises(ValueError, match="Missing mandatory parameter '--custom-grid'"):
        create_grid_coordinates("custom")

    # 3. Stereographic grid raises error if mandatory EXTENT_DEG is missing
    with pytest.raises(ValueError, match="EXTENT_DEG"):
        create_grid_coordinates("stereographic")


def test_create_stereographic_grid() -> None:
    """Test general stereographic grid generation using mandatory EXTENT_DEG over discrete dimensions."""
    # 1. Polar center with mandatory arc degree option
    lon1, lat1 = create_stereographic_grid(
        CENTER_LON=0.0,
        CENTER_LAT=90.0,
        EXTENT_DEG=4.5,
        NX=11,
        NY=11,
    )
    assert lon1.shape == (11, 11)
    assert lat1.shape == (11, 11)
    cy, cx = lon1.shape[0] // 2, lon1.shape[1] // 2
    assert np.isclose(lat1[cy, cx], 90.0, atol=1e-3)
    # Distance from center (cy, cx) to edges: (0, cx), (NY-1, cx), (cy, 0), (cy, NX-1)
    # Center is at lat 90.0, so edge latitude should be 90.0 - EXTENT_DEG = 85.5
    assert np.isclose(lat1[0, cx], 90.0 - 4.5, atol=1e-3)
    assert np.isclose(lat1[10, cx], 90.0 - 4.5, atol=1e-3)
    assert np.isclose(lat1[cy, 0], 90.0 - 4.5, atol=1e-3)
    assert np.isclose(lat1[cy, 10], 90.0 - 4.5, atol=1e-3)

    # 2. Non-square grid (NY < NX): extent applies to smaller dimension NY
    lon_rect, lat_rect = create_stereographic_grid(
        CENTER_LON=0.0,
        CENTER_LAT=90.0,
        EXTENT_DEG=10.0,
        NX=21,
        NY=11,
    )
    assert lon_rect.shape == (11, 21)
    cy_r, cx_r = 5, 10
    assert np.isclose(lat_rect[cy_r, cx_r], 90.0, atol=1e-3)
    # The smaller dimension is NY (11), so from center to top/bottom edge is exactly 10.0 deg
    assert np.isclose(lat_rect[0, cx_r], 80.0, atol=1e-3)
    assert np.isclose(lat_rect[10, cx_r], 80.0, atol=1e-3)

    # 3. Oblique center
    lon2, lat2 = create_stereographic_grid(
        CENTER_LON=-75.0,
        CENTER_LAT=40.0,
        EXTENT_DEG=5.0,
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
        EXTENT_DEG=4.5,
        NX=11,
        NY=11,
        ROTATION=45.0,
    )
    assert lon_rot.shape == (11, 11)
    assert lat_rot.shape == (11, 11)
    assert np.isclose(lat_rot[cy, cx], 90.0, atol=1e-3)

    # 5. Missing EXTENT_DEG raises ValueError
    with pytest.raises(ValueError, match="EXTENT_DEG is mandatory"):
        create_stereographic_grid(CENTER_LON=0.0, CENTER_LAT=90.0, EXTENT_DEG=None)


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

    # 3. General Stereographic in arc degrees
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


def test_create_regular_grid_global_closure() -> None:
    """Test creating a regular grid with global_closure=True calculates sx=360/NX and lon_end."""
    lon, lat = create_regular_grid(
        LON_START=0.0,
        LAT_START=-90.0,
        LAT_END=90.0,
        NX=1440,
        NY=721,
        global_closure=True,
    )
    assert lon.shape == (721, 1440)
    assert lat.shape == (721, 1440)
    assert np.isclose(lon[0, 0], 0.0)
    assert np.isclose(lon[0, -1], 359.75)
    assert np.isclose(lat[0, 0], -90.0)
    assert np.isclose(lat[-1, 0], 90.0)


def test_create_regular_grid_with_increments() -> None:
    """Test creating a regular grid using mandatory lower corner coordinates and grid increments (SX, SY)."""
    lon, lat = create_regular_grid(
        LON_START=20.0,
        LAT_START=-75.0,
        SX=0.25,
        SY=0.25,
        NX=1440,
        NY=601,
    )
    assert lon.shape == (601, 1440)
    assert lat.shape == (601, 1440)
    assert np.isclose(lon[0, 0], 20.0)
    assert np.isclose(lon[0, -1], 379.75)
    assert np.isclose(lat[0, 0], -75.0)
    assert np.isclose(lat[-1, 0], 75.0)


def test_create_regular_grid_optional_defaults() -> None:
    """Test that create_regular_grid uses default starting points when omitted."""
    lon, lat = create_regular_grid(NX=10, NY=10)
    assert lon.shape == (10, 10)
    assert lat.shape == (10, 10)
    assert np.isclose(lon[0, 0], 0.0)
    assert np.isclose(lat[0, 0], -90.0)


def test_gridgen_grid_reexports() -> None:
    """Verify coordinate routines are re-exported and accessible from gridgen.grid."""
    from gridgen.grid import (
        create_grid_coordinates as cgc,
    )
    from gridgen.grid import (
        create_regular_grid as crg,
    )

    lon, lat = crg(
        LON_START=0.0,
        LAT_START=0.0,
        SX=1.0,
        SY=1.0,
        NX=11,
        NY=11,
    )
    assert lon.shape == (11, 11)
    assert lat.shape == (11, 11)
    assert np.isclose(lon[0, -1], 10.0)
    assert np.isclose(lat[-1, 0], 10.0)

    lon2, lat2 = cgc(
        "regular",
        LON_START=0.0,
        LAT_START=0.0,
        LON_END=10.0,
        LAT_END=10.0,
        NX=11,
        NY=11,
    )
    assert np.allclose(lon, lon2)
    assert np.allclose(lat, lat2)


def test_geo_rotated_coordinate_transforms_roundtrip() -> None:
    """Test round-trip conversions between geographic and rotated coordinates."""
    pole_lon = 180.0
    pole_lat = 60.0

    # 1. Scalar coordinate round-trip
    orig_lon, orig_lat = 135.0, 35.0
    rlon, rlat = geo_to_rotated_coords(orig_lon, orig_lat, pole_lon, pole_lat)
    assert isinstance(rlon, float)
    assert isinstance(rlat, float)

    rec_lon, rec_lat = rotated_to_geo_coords(rlon, rlat, pole_lon, pole_lat)
    assert isinstance(rec_lon, float)
    assert isinstance(rec_lat, float)
    assert np.isclose(rec_lon, orig_lon)
    assert np.isclose(rec_lat, orig_lat)

    # 2. Array coordinate round-trip
    lons = np.array([0.0, 45.0, 180.0, 270.0])
    lats = np.array([-30.0, 0.0, 45.0, 60.0])
    rlons, rlats = geo_to_rotated_coords(lons, lats, pole_lon, pole_lat)
    rec_lons, rec_lats = rotated_to_geo_coords(rlons, rlats, pole_lon, pole_lat)
    assert np.allclose(rec_lons, lons)
    assert np.allclose(rec_lats, lats)


def test_create_regular_grid_rotated_pole_center_alignment() -> None:
    """Test 4-step algorithm in create_regular_grid with rotated pole."""
    pole_lon = 180.0
    pole_lat = 60.0

    lon_start, lon_end = 120.0, 140.0
    lat_start, lat_end = 20.0, 40.0
    nx, ny = 21, 21

    lon, lat = create_regular_grid(
        LON_START=lon_start,
        LON_END=lon_end,
        LAT_START=lat_start,
        LAT_END=lat_end,
        NX=nx,
        NY=ny,
        POLE_LON=pole_lon,
        POLE_LAT=pole_lat,
    )

    assert lon.shape == (ny, nx)
    assert lat.shape == (ny, nx)

    # Verify center point in traditional lon-lat space matches the center of the generated grid
    center_lon_expected = 0.5 * (lon_start + lon_end)
    center_lat_expected = 0.5 * (lat_start + lat_end)

    center_i = nx // 2
    center_j = ny // 2

    assert np.isclose(lon[center_j, center_i], center_lon_expected, atol=1e-5)
    assert np.isclose(lat[center_j, center_i], center_lat_expected, atol=1e-5)

    # Verify resolution in rotated coordinates matches expected SX and SY
    rlon_all, rlat_all = geo_to_rotated_coords(lon, lat, pole_lon, pole_lat)
    sx_expected = (lon_end - lon_start) / (nx - 1)
    sy_expected = (lat_end - lat_start) / (ny - 1)

    diff_rlon = np.diff(rlon_all, axis=1)
    diff_rlat = np.diff(rlat_all, axis=0)

    assert np.allclose(diff_rlon, sx_expected, atol=1e-5)
    assert np.allclose(diff_rlat, sy_expected, atol=1e-5)
