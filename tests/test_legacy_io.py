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

from gridgen.io.ascii import write_ww3file, write_ww3meta, write_ww3obstr
from gridgen.io.coards import nc_ww3_grdwrite


def test_write_ww3file(tmp_path):
    data = np.array([[10, 20], [30, 40]], dtype=float)
    filepath = str(tmp_path / "test.depth_ascii")

    _msg, err = write_ww3file(filepath, data)
    assert err == 0
    assert os.path.exists(filepath)

    with open(filepath) as f:
        content = f.read()
    assert "10 20" in content
    assert "30 40" in content


def test_write_ww3obstr(tmp_path):
    d1 = np.array([[10, 20], [30, 40]], dtype=float)
    d2 = np.array([[50, 60], [70, 80]], dtype=float)
    filepath = str(tmp_path / "test.obstr_lev1")

    _msg, err = write_ww3obstr(filepath, d1, d2)
    assert err == 0
    assert os.path.exists(filepath)

    with open(filepath) as f:
        content = f.read()
    assert "10 20" in content
    assert "50 60" in content


def test_write_ww3meta(tmp_path):
    lon1d = np.array([10.0, 11.0, 12.0])
    lat1d = np.array([20.0, 21.0, 22.0])
    lon, lat = np.meshgrid(lon1d, lat1d)
    filepath = str(tmp_path / "test")

    _msg, err = write_ww3meta(filepath, "RECT", lon, lat)
    assert err == 0
    assert os.path.exists(filepath + ".meta")

    with open(filepath + ".meta") as f:
        content = f.read()
    assert "RECT" in content
    assert "Bottom Bathymetry" in content


def test_nc_ww3_grdwrite(tmp_path):
    lon1d = np.array([10.0, 11.0, 12.0])
    lat1d = np.array([20.0, 21.0, 22.0])
    lon, lat = np.meshgrid(lon1d, lat1d)
    z = np.ones((3, 3), dtype=float) * 10.0
    mask = np.ones((3, 3), dtype=float)
    sx = np.zeros((3, 3), dtype=float)
    sy = np.zeros((3, 3), dtype=float)

    filepath = str(tmp_path / "test_coards.nc")
    nc_ww3_grdwrite(lon, lat, z, filepath, mask=mask, sx=sx, sy=sy)

    assert os.path.exists(filepath)
    ds = xr.open_dataset(filepath)
    assert "z" in ds
    assert "mask" in ds
    assert "sx" in ds
    assert "sy" in ds
    assert ds.attrs["Conventions"] == "COARDS/CF-1.0"
    ds.close()
