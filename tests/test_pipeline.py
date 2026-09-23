# WAVEWATCH IV (WW4) Gridgen Package Tests
#
# Copyright 2026 National Weather Service (NWS), NOAA. All rights reserved.
# NWS often uses Generative AI (GenAI) for code development and refactoring.
# Whenever GenAI is used, NWS requires a full human review of code before it
# is added to its repositories.
#
# @author Aldgisl (Agentic AI)
# @author Hendrik Tolman
# @date Initial: 2026-05-20
# @date Update: 2026-05-20

from __future__ import annotations

import os

import numpy as np
import xarray as xr

from gridgen.grid import generate_grid
from gridgen.io.ugrid import create_ugrid_dataset, write_ugrid_nc
from gridgen.io.zarr_store import write_ugrid_zarr
from gridgen.masking import clean_mask, remove_lake
from gridgen.obstructions import create_obstr


def test_full_grid_pipeline(tmp_path):
    lon1d = np.array([10.0, 11.0, 12.0, 13.0])
    lat1d = np.array([20.0, 21.0, 22.0, 23.0])
    lon, lat = np.meshgrid(lon1d, lat1d)

    # 1. Generate bathymetry
    depth = generate_grid(lon, lat)
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

    # 4. UGRID & Zarr export
    ds_ugrid = create_ugrid_dataset(
        lon, lat, depth, mask_mod, sx=sx, sy=sy, title="Pipeline Test"
    )

    nc_out = str(tmp_path / "pipeline.nc")
    zarr_out = str(tmp_path / "pipeline.zarr")

    write_ugrid_nc(ds_ugrid, nc_out)
    write_ugrid_zarr(ds_ugrid, zarr_out)

    assert os.path.exists(nc_out)
    assert os.path.exists(zarr_out)

    ds_nc = xr.open_dataset(nc_out)
    ds_zr = xr.open_zarr(zarr_out)

    assert ds_nc.attrs["Conventions"] == "CF-1.8 UGRID-1.0"
    assert ds_zr.attrs["Conventions"] == "CF-1.8 UGRID-1.0"

    ds_nc.close()
    ds_zr.close()
