# WAVEWATCH III (WW3) / WAVEWATCH IV (WW4) Gridgen Package Tests
#
# Copyright 2026 National Weather Service (NWS), NOAA. All rights reserved.
# NWS often uses Generative AI (GenAI) for code development and refactoring.
# Whenever GenAI is used, NWS requires a full human review of code before it
# is added to its repositories.
#
# @author Aldgisl (Agentic AI), Jules (Agentic AI), Hendrik Tolman
# @date Initial: 2026-10-05

from __future__ import annotations

import os

import matplotlib
import numpy as np

# Force non-interactive Agg backend for testing
matplotlib.use("Agg")

from gridgen.io.ascii import write_ww3file, write_ww3meta, write_ww3obstr
from gridgen.io.coards import nc_ww3_grdwrite
from gridgen.io.ugrid import create_ugrid_dataset, write_ugrid_nc
from gridgen.vis import load_grid_data, plot_grid


def test_vis_ugrid(tmp_path):
    lon1d = np.array([10.0, 11.0, 12.0])
    lat1d = np.array([20.0, 21.0, 22.0])
    lon, lat = np.meshgrid(lon1d, lat1d)
    depth = np.array([[10.0, 20.0, 30.0], [15.0, 25.0, 35.0], [10.0, 10.0, 10.0]])
    mask = np.ones((3, 3), dtype=int)
    sx = np.full((3, 3), 0.1)
    sy = np.full((3, 3), 0.2)

    ds = create_ugrid_dataset(lon, lat, depth, mask, sx=sx, sy=sy, title="Test Vis Grid")
    nc_path = str(tmp_path / "test_vis_ugrid.nc")
    write_ugrid_nc(ds, nc_path)

    data = load_grid_data(nc_path)
    assert "lon" in data
    assert "lat" in data
    assert "depth" in data
    assert "sx" in data
    assert "sy" in data
    assert data["depth"].shape == (3, 3)

    out_gif = str(tmp_path / "vis_ugrid.gif")
    fig = plot_grid(data, title="UGRID Vis Test", output_path=out_gif)
    assert os.path.exists(out_gif)
    assert fig is not None


def test_vis_coards(tmp_path):
    lon1d = np.array([10.0, 11.0, 12.0])
    lat1d = np.array([20.0, 21.0, 22.0])
    lon, lat = np.meshgrid(lon1d, lat1d)
    depth = np.full((3, 3), 50.0)
    mask = np.ones((3, 3), dtype=int)
    sx = np.zeros((3, 3))
    sy = np.zeros((3, 3))

    nc_path = str(tmp_path / "test_coards.nc")
    nc_ww3_grdwrite(lon, lat, depth, nc_path, mask=mask, sx=sx, sy=sy)

    data = load_grid_data(nc_path)
    assert data["depth"].shape == (3, 3)

    out_gif = str(tmp_path / "vis_coards.gif")
    fig = plot_grid(data, title="COARDS Vis Test", output_path=out_gif)
    assert os.path.exists(out_gif)
    assert fig is not None


def test_vis_ascii(tmp_path):
    Ny, Nx = 3, 3
    lon1d = np.linspace(10.0, 12.0, Nx)
    lat1d = np.linspace(20.0, 22.0, Ny)
    lon, lat = np.meshgrid(lon1d, lat1d)

    depth = np.array([[10.0, 20.0, 30.0], [15.0, 25.0, 35.0], [10.0, 10.0, 10.0]])
    mask = np.ones((Ny, Nx), dtype=int)
    sx = np.full((Ny, Nx), 0.05)
    sy = np.full((Ny, Nx), 0.15)

    prefix = str(tmp_path / "ww3_ascii_test")
    depth_scale = 1000.0
    obstr_scale = 100.0
    write_ww3file(f"{prefix}.depth_ascii", depth * depth_scale)
    write_ww3file(f"{prefix}.maskorig_ascii", mask)
    write_ww3obstr(f"{prefix}.obstr_lev1", sx * obstr_scale, sy * obstr_scale)
    write_ww3meta(prefix, "RECT", lon, lat, 1.0 / depth_scale, 1.0 / obstr_scale, 1.0)

    data = load_grid_data(prefix)
    assert data["depth"].shape == (3, 3)
    assert np.allclose(data["sx"], sx)

    out_gif = str(tmp_path / "vis_ascii.gif")
    fig = plot_grid(data, title="ASCII Vis Test", output_path=out_gif)
    assert os.path.exists(out_gif)
    assert fig is not None
