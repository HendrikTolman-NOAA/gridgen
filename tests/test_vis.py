# WAVEWATCH III (WW3) / WAVEWATCH IV (WW4) Gridgen Package Tests
#
# Copyright 2026 National Weather Service (NWS), NOAA. All rights reserved.
# NWS often uses Generative AI (GenAI) for code development and refactoring.
# Whenever GenAI is used, NWS requires a full human review of code before it
# is added to its repositories.
#
# @author Aldgisl (Agentic AI), Hendrik Tolman
# @author Jules (Agentic AI) (contributor)
# @date Initial: 2026-10-05
# @date Latest Update: 2026-10-06

from __future__ import annotations

import os
import subprocess
from pathlib import Path

import matplotlib
import numpy as np
from PIL import Image

# Force non-interactive Agg backend for testing
matplotlib.use("Agg")

from gridgen.io.ascii import write_ww3file, write_ww3meta, write_ww3obstr
from gridgen.io.coards import nc_ww3_grdwrite
from gridgen.io.ugrid import create_ugrid_dataset, write_ugrid_nc
from gridgen.vis import extract_grid_name, load_grid_data, plot_grid


def test_extract_grid_name():
    assert extract_grid_name("ww4_grid_ugrid.nc") == "ww4_grid"
    assert extract_grid_name("/path/to/mygrid_coards.nc") == "mygrid"
    assert extract_grid_name("test.depth_ascii") == "test"


def test_vis_ugrid(tmp_path):
    lon1d = np.array([10.0, 11.0, 12.0])
    lat1d = np.array([20.0, 21.0, 22.0])
    lon, lat = np.meshgrid(lon1d, lat1d)
    depth = np.array([[10.0, 20.0, 30.0], [15.0, 25.0, 35.0], [10.0, 10.0, 10.0]])
    mask = np.ones((3, 3), dtype=int)
    sx = np.full((3, 3), 0.1)
    sy = np.full((3, 3), 0.2)

    ds = create_ugrid_dataset(
        lon, lat, depth, mask, sx=sx, sy=sy, title="Test Vis Grid"
    )
    nc_path = str(tmp_path / "test_vis_ugrid.nc")
    write_ugrid_nc(ds, nc_path)

    data = load_grid_data(nc_path)
    assert "lon" in data
    assert "lat" in data
    assert "depth" in data
    assert "sx" in data
    assert "sy" in data
    assert data["depth"].shape == (3, 3)

    for ext in ["jpg", "pdf", "eps", "gif", "png"]:
        out_file = str(tmp_path / f"vis_ugrid.{ext}")
        fig = plot_grid(data, title="UGRID Vis Test", output_path=out_file)
        assert os.path.exists(out_file)
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


def test_view_grid_script_help():
    """Verify that view_grid.sh executes and returns usage help message."""
    repo_root = Path(__file__).parent.parent
    script_path = repo_root / "view_grid.sh"

    assert script_path.exists(), "view_grid.sh must exist"
    assert os.access(script_path, os.X_OK), "script must be executable"

    result = subprocess.run(
        [str(script_path), "--help"],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    assert "Usage: ./view_grid.sh" in result.stdout


def test_view_grid_script_missing_file(tmp_path: Path):
    """Verify view_grid.sh error reporting when specified image file does not exist."""
    repo_root = Path(__file__).parent.parent
    script_path = repo_root / "view_grid.sh"
    non_existent_img = tmp_path / "non_existent_plot.jpg"

    result = subprocess.run(
        [str(script_path), str(non_existent_img)],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode != 0
    assert "Grid graphics image file not found" in result.stderr


def test_view_grid_script_display_check(tmp_path: Path):
    """Verify view_grid.sh execution and DISPLAY troubleshooting message when DISPLAY is unset."""
    repo_root = Path(__file__).parent.parent
    script_path = repo_root / "view_grid.sh"

    # Create dummy image file
    dummy_img = tmp_path / "test_view_grid.jpg"
    Image.new("RGB", (50, 50), color="red").save(dummy_img)

    env = os.environ.copy()
    env.pop("DISPLAY", None)
    env.pop("WAYLAND_DISPLAY", None)

    result = subprocess.run(
        [str(script_path), str(dummy_img)],
        capture_output=True,
        text=True,
        env=env,
        check=False,
    )

    assert result.returncode == 0
    assert "Displaying WAVEWATCH Grid Graphics" in result.stdout
    assert (
        "WARNING: Neither DISPLAY nor WAYLAND_DISPLAY environment variable is set."
        in result.stdout
    )
    assert "Troubleshooting steps to display graphics" in result.stdout


def test_plot_grid_from_external_directory_default_out(tmp_path: Path):
    """Verify plot_grid.sh executed from an external working directory defaults output figure location to repo_root."""
    repo_root = Path(__file__).parent.parent
    script_path = repo_root / "plot_grid.sh"

    # Create dummy NetCDF UGRID file in repo_root
    lon1d = np.array([10.0, 11.0, 12.0])
    lat1d = np.array([20.0, 21.0, 22.0])
    lon, lat = np.meshgrid(lon1d, lat1d)
    depth = np.full((3, 3), 10.0)
    mask = np.ones((3, 3), dtype=int)
    ds = create_ugrid_dataset(lon, lat, depth, mask, title="Ext Grid Plot Test")

    grid_name = "ext_plot_test"
    nc_file = repo_root / f"{grid_name}_ugrid.nc"
    write_ugrid_nc(ds, str(nc_file))

    try:
        result = subprocess.run(
            [str(script_path), "-i", str(nc_file), "-f", "jpg", "--no-display"],
            cwd=tmp_path,
            capture_output=True,
            text=True,
            check=False,
        )

        assert result.returncode == 0
        # Default output graphic should be placed in repo_root
        expected_plot = repo_root / f"{grid_name}.jpg"
        assert expected_plot.exists()
        assert not (tmp_path / f"{grid_name}.jpg").exists()
    finally:
        if nc_file.exists():
            nc_file.unlink()
        plot_path = repo_root / f"{grid_name}.jpg"
        if plot_path.exists():
            plot_path.unlink()


def test_plot_grid_from_external_directory_custom_out(tmp_path: Path):
    """Verify plot_grid.sh executed from external directory respects relative user output figure path."""
    repo_root = Path(__file__).parent.parent
    script_path = repo_root / "plot_grid.sh"

    lon1d = np.array([10.0, 11.0, 12.0])
    lat1d = np.array([20.0, 21.0, 22.0])
    lon, lat = np.meshgrid(lon1d, lat1d)
    depth = np.full((3, 3), 10.0)
    mask = np.ones((3, 3), dtype=int)
    ds = create_ugrid_dataset(lon, lat, depth, mask, title="Ext Custom Plot Test")

    nc_file = tmp_path / "custom_input_ugrid.nc"
    write_ugrid_nc(ds, str(nc_file))

    out_jpg = "my_external_plot.jpg"

    result = subprocess.run(
        [
            str(script_path),
            "-i",
            str(nc_file),
            "-o",
            out_jpg,
            "-f",
            "jpg",
            "--no-display",
        ],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    # Output file should be created inside tmp_path (where user ran it)
    assert (tmp_path / out_jpg).exists()


def test_bin_plot_grid_py_from_external_directory(tmp_path: Path):
    """Verify bin/plot_grid.py executed from external directory runs correctly and places output as specified."""
    repo_root = Path(__file__).parent.parent
    bin_script = repo_root / "bin" / "plot_grid.py"

    lon1d = np.array([10.0, 11.0, 12.0])
    lat1d = np.array([20.0, 21.0, 22.0])
    lon, lat = np.meshgrid(lon1d, lat1d)
    depth = np.full((3, 3), 10.0)
    mask = np.ones((3, 3), dtype=int)
    ds = create_ugrid_dataset(lon, lat, depth, mask, title="Bin Plot Test")

    nc_file = tmp_path / "bin_plot_input_ugrid.nc"
    write_ugrid_nc(ds, str(nc_file))

    out_jpg = "bin_ext_plot.jpg"

    result = subprocess.run(
        [
            "python3",
            str(bin_script),
            "-i",
            str(nc_file),
            "-o",
            out_jpg,
            "-f",
            "jpg",
            "--no-display",
        ],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    assert (tmp_path / out_jpg).exists()
