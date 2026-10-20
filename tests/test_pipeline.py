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
# @date Latest Update: 2026-10-06

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
    sx, sy = create_obstr(lon, lat, [], mask_mod)
    assert sx.shape == (4, 4)
    assert sy.shape == (4, 4)

    # 4. UGRID export
    ds_ugrid = create_ugrid_dataset(
        lon, lat, depth, mask_mod, sx=sx, sy=sy, title="Pipeline Test"
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
