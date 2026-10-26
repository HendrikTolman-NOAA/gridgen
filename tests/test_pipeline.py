# WAVEWATCH III (WW3) / WAVEWATCH IV (WW4) Gridgen Package Tests
#
# Copyright 2026 National Weather Service (NWS), NOAA. All rights reserved.
# NWS often uses Generative AI (GenAI) for code development and refactoring.
# Whenever GenAI is used, NWS requires a full human review of code before it
# is added to its repositories.
#
# @author Aldgisl (Agentic AI), Hendrik Tolman
# @author Jules (Agentic AI) (contributor)
# @date Initial: 2026-09-22
# @date Latest Update: 2026-10-20

from __future__ import annotations

import os

import numpy as np
import xarray as xr

from gridgen.grid import generate_grid
from gridgen.io.ugrid import create_ugrid_dataset, write_ugrid_nc
from gridgen.masking import clean_mask, remove_lake
from gridgen.obstructions import create_obstr


def test_full_grid_pipeline(tmp_path):
    lon1d = np.array([10.0, 11.0, 12.0, 13.0])
    lat1d = np.array([20.0, 21.0, 22.0, 23.0])
    lon, lat = np.meshgrid(lon1d, lat1d)

    # 1. Generate bathymetry using synthetic dataset
    z = np.full((4, 4), -50.0)
    ds_mock = xr.Dataset(
        data_vars={"z": (("lat", "lon"), z)},
        coords={"lon": lon1d, "lat": lat1d},
    )
    depth = generate_grid(lon, lat, bathy_source=ds_mock)
    assert depth.shape == (4, 4)

    # 2. Masking
    mask = np.ones((4, 4), dtype=int)
    mask[0, 0] = 0
    clean_m = clean_mask(lon, lat, mask, [])
    mask_mod, _mask_map = remove_lake(clean_m, lake_tol=-1, igl=0)

    # 3. Obstructions
    ObsX, ObsY = create_obstr(lon, lat, [], mask_mod)
    assert ObsX.shape == (4, 4)
    assert ObsY.shape == (4, 4)

    # 4. UGRID export
    ds_ugrid = create_ugrid_dataset(
        lon, lat, depth, mask_mod, ObsX=ObsX, ObsY=ObsY, title="Pipeline Test"
    )

    nc_out = str(tmp_path / "pipeline.nc")

    write_ugrid_nc(ds_ugrid, nc_out)

    assert os.path.exists(nc_out)

    ds_nc = xr.open_dataset(nc_out)

    assert ds_nc.attrs["Conventions"] == "CF-1.8 UGRID-1.0"

    ds_nc.close()


def test_generate_grid_wraparound_performance_and_correctness():
    """Test bathymetry extraction across 180° / 360° longitude wraparound boundaries."""
    from gridgen.coordinates import create_regular_grid

    # Synthetic fine bathymetry dataset spanning [-180, 180]
    lon_b = np.linspace(-180.0, 180.0, 3600)
    lat_b = np.linspace(-90.0, 90.0, 1800)
    z_b = np.full((len(lat_b), len(lon_b)), -100.0)

    ds_mock = xr.Dataset(
        data_vars={"z": (("y", "x"), z_b)},
        coords={"x": lon_b, "y": lat_b},
    )

    # Grid spanning [20, 379.75] longitude, which includes the 180° wraparound point
    lon, lat = create_regular_grid(
        LON_START=20.0,
        LON_END=379.75,
        LAT_START=-75.0,
        LAT_END=75.0,
        NX=180,
        NY=77,
    )

    import time

    t0 = time.time()
    depth = generate_grid(lon, lat, bathy_source=ds_mock)
    elapsed = time.time() - t0

    assert depth.shape == (77, 180)
    assert np.all(depth <= 0.1)  # wet cells should be -100.0
    assert elapsed < 15.0  # extraction must complete quickly without slowdown


def test_gebco_bathymetry_source_loading(tmp_path):
    """Test loading GEBCO NetCDF dataset files with descending coordinates and auto variable detection."""
    lon1d = np.linspace(-180.0, 180.0, 360)
    lat1d = np.linspace(90.0, -90.0, 180)  # Descending latitude as in GEBCO NetCDF
    elevation = np.full((len(lat1d), len(lon1d)), -200.0)

    ds_gebco = xr.Dataset(
        data_vars={"elevation": (("lat", "lon"), elevation)},
        coords={"lon": lon1d, "lat": lat1d},
    )

    # Save mock GEBCO file gebco_2024.nc
    gebco_path = tmp_path / "gebco_2024.nc"
    ds_gebco.to_netcdf(gebco_path)

    lon_grid, lat_grid = np.meshgrid(
        np.linspace(-10.0, 10.0, 5), np.linspace(-10.0, 10.0, 5)
    )

    # Test loading using bathy_source="gebco_2024"
    depth_2024 = generate_grid(
        lon_grid, lat_grid, ref_dir=str(tmp_path), bathy_source="gebco_2024"
    )
    assert depth_2024.shape == (5, 5)
    assert np.allclose(depth_2024, -200.0)

    # Test loading using bathy_source="gebco" alias
    depth_alias = generate_grid(
        lon_grid, lat_grid, ref_dir=str(tmp_path), bathy_source="gebco"
    )
    assert depth_alias.shape == (5, 5)
    assert np.allclose(depth_alias, -200.0)

    # Test direct Dataset loading with auto-detection
    depth_ds = generate_grid(lon_grid, lat_grid, bathy_source=ds_gebco)
    assert depth_ds.shape == (5, 5)
    assert np.allclose(depth_ds, -200.0)


def test_remove_lake_keep_lakes_and_global_closure():
    """Test lake removal tolerance options and global closure wrap-around connection."""
    # Create mask with ocean spanning col 0 and col 9 (global closure), and a separate lake
    mask = np.zeros((5, 10), dtype=int)
    mask[2, 0] = 1  # Ocean left boundary
    mask[2, 1] = 1
    mask[2, 8] = 1
    mask[2, 9] = 1  # Ocean right boundary (connected if igl=1)
    mask[4, 4] = 1  # Isolated small lake

    lon1d = np.linspace(0.0, 360.0, 10)
    lat1d = np.linspace(-10.0, 10.0, 5)
    lon, _ = np.meshgrid(lon1d, lat1d)

    # 1. With min_lake_points=0 and min_lake_fraction=0.0 (preserve all lakes)
    m_keep, _ = remove_lake(mask, min_lake_points=0, min_lake_fraction=0.0, lon=lon)
    assert m_keep[4, 4] == 1  # Lake preserved

    # 2. With default thresholds (min_lake_points=15, min_lake_fraction=0.0005) and global closure
    m_closure, _ = remove_lake(mask, min_lake_points=15, min_lake_fraction=0.0005, igl=0, lon=lon)
    # Ocean on col 0 and col 9 should be merged as one contiguous ocean body (size 4)
    # The small lake at (4,4) (size 1) should be removed as it is below min_lake_points (15)
    assert m_closure[2, 0] == 1
    assert m_closure[2, 9] == 1
    assert m_closure[4, 4] == 0  # Lake removed


def test_create_obstr_adjacency_zeroing():
    """Test subgrid obstruction calculation and dry neighbor zeroing behavior."""
    from shapely.geometry import Polygon

    # 3x3 grid spanning [0, 3] degrees in lon and lat
    lon1d = np.array([0.5, 1.5, 2.5])
    lat1d = np.array([0.5, 1.5, 2.5])
    lon, lat = np.meshgrid(lon1d, lat1d)

    # Polygon covering part of cell (1, 1) [lon 1.0..2.0, lat 1.0..2.0]
    # Island polygon inside cell (1, 1) spanning lon [1.2, 1.8] and lat [1.2, 1.8]
    poly_dict = {
        "x": np.array([1.2, 1.8, 1.8, 1.2, 1.2]),
        "y": np.array([1.2, 1.2, 1.8, 1.8, 1.2]),
        "level": 1,
        "polygon": Polygon([(1.2, 1.2), (1.8, 1.2), (1.8, 1.8), (1.2, 1.8), (1.2, 1.2)]),
    }

    # Scenario A: All cells wet (mask=1)
    mask_all_wet = np.ones((3, 3), dtype=int)
    ObsX, ObsY = create_obstr(lon, lat, [poly_dict], mask_all_wet)

    # Cell (1, 1) intersects island polygon
    # Height = 1.0, Width = 1.0, poly height = 0.6, poly width = 0.6 -> ratio 0.6
    assert np.isclose(ObsX[1, 1], 0.6)
    assert np.isclose(ObsY[1, 1], 0.6)

    # Scenario B: East neighbor cell (1, 2) is dry (mask=0)
    # ObsX[1, 1] checks horizontal neighbors (j+1, j-1) and is zeroed when East cell is dry.
    # ObsY[1, 1] checks vertical neighbors (k+1, k-1) and is preserved when vertical neighbors are wet.
    mask_dry_east = np.ones((3, 3), dtype=int)
    mask_dry_east[1, 2] = 0

    ObsX_b, ObsY_b = create_obstr(lon, lat, [poly_dict], mask_dry_east)

    assert ObsX_b[1, 1] == 0.0
    assert np.isclose(ObsY_b[1, 1], 0.6)
