# WAVEWATCH III (WW3) / WAVEWATCH IV (WW4) Gridgen Package Tests
#
# Copyright 2026 National Weather Service (NWS), NOAA. All rights reserved.
# NWS often uses Generative AI (GenAI) for code development and refactoring.
# Whenever GenAI is used, NWS requires a full human review of code before it
# is added to its repositories.
#
# @author Aldgisl (Agentic AI), Hendrik Tolman
# @date Initial: 2026-09-22

from __future__ import annotations

import os

import numpy as np
import xarray as xr

from gridgen.io.ugrid import create_ugrid_dataset, write_ugrid_nc
from gridgen.io.zarr_store import write_ugrid_zarr


def test_ugrid_nc_export(tmp_path):
    lon1d = np.array([10.0, 11.0, 12.0])
    lat1d = np.array([20.0, 21.0, 22.0])
    lon, lat = np.meshgrid(lon1d, lat1d)
    depth = np.full((3, 3), 10.0)
    mask = np.ones((3, 3), dtype=int)
    sx = np.zeros((3, 3))
    sy = np.zeros((3, 3))

    ds = create_ugrid_dataset(
        lon, lat, depth, mask, sx=sx, sy=sy, title="Test UGRID Grid"
    )

    assert "mesh_topology" in ds
    assert ds["mesh_topology"].attrs["cf_role"] == "mesh_topology"
    assert ds["mesh_topology"].attrs["topology_dimension"] == 2
    assert "face_node_connectivity" in ds
    assert ds["face_node_connectivity"].attrs["cf_role"] == "face_node_connectivity"
    assert "depth" in ds
    assert ds["depth"].attrs["mesh"] == "mesh_topology"
    assert ds["depth"].attrs["location"] == "face"

    nc_path = str(tmp_path / "test_ugrid.nc")
    write_ugrid_nc(ds, nc_path)
    assert os.path.exists(nc_path)

    ds_read = xr.open_dataset(nc_path)
    assert "depth" in ds_read
    assert ds_read.attrs["Conventions"] == "CF-1.8 UGRID-1.0"
    ds_read.close()


def test_ugrid_zarr_export(tmp_path):
    lon1d = np.array([10.0, 11.0, 12.0])
    lat1d = np.array([20.0, 21.0, 22.0])
    lon, lat = np.meshgrid(lon1d, lat1d)
    depth = np.full((3, 3), 15.0)
    mask = np.ones((3, 3), dtype=int)

    ds = create_ugrid_dataset(lon, lat, depth, mask, title="Test Zarr Store")

    zarr_path = str(tmp_path / "test_ugrid.zarr")
    write_ugrid_zarr(ds, zarr_path, chunks={"nMesh2_face": 3})
    assert os.path.exists(zarr_path)

    ds_zarr = xr.open_zarr(zarr_path)
    assert "depth" in ds_zarr
    assert ds_zarr["depth"].shape == (9,)
    assert ds_zarr.attrs["Conventions"] == "CF-1.8 UGRID-1.0"
    ds_zarr.close()
