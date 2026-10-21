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
# @date Latest Update: 2026-10-21

from __future__ import annotations

import os
import subprocess
from pathlib import Path

import matplotlib
import numpy as np

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


def test_fmt_lon_and_lat():
    from gridgen.vis import fmt_lat, fmt_lon

    assert fmt_lon(0) == "0°"
    assert fmt_lon(90) == "90°E"
    assert fmt_lon(180) == "180°"
    assert fmt_lon(270) == "90°W"
    assert fmt_lon(360) == "0°"

    assert fmt_lat(0) == "0°"
    assert fmt_lat(45) == "45°N"
    assert fmt_lat(-45) == "45°S"


def test_vis_orography_and_mask(tmp_path):
    """Verify plot_grid handles bathymetry (depth <= 0), orography (depth > 0) with 10m cap, and dark green mask."""
    lon1d = np.array([10.0, 11.0, 12.0])
    lat1d = np.array([20.0, 21.0, 22.0])
    lon, lat = np.meshgrid(lon1d, lat1d)
    # Include negative depth (bathymetry), positive depth (orography), and high dry land
    depth = np.array([[-100.0, -50.0, -10.0], [5.0, 15.0, 25.0], [999999.0, 999999.0, 999999.0]])
    mask = np.array([[1, 1, 1], [1, 1, 1], [0, 0, 0]])

    data = {"lon": lon, "lat": lat, "depth": depth, "mask": mask}
    out_file = str(tmp_path / "test_orog_mask.jpg")

    fig = plot_grid(data, title="Orography Test", output_path=out_file, max_orography=10.0)
    assert fig is not None
    assert os.path.exists(out_file)

    ax = fig.axes[0]
    assert ax.get_facecolor() == (0.10588235294117647, 0.2627450980392157, 0.19607843137254902, 1.0)  # #1b4332 in RGBA


def test_vis_orography_scale_when_no_orography(tmp_path):
    """Verify plot_grid displays 'Grid contains no orography' statement when no land points exist."""
    lon1d = np.array([10.0, 11.0, 12.0])
    lat1d = np.array([20.0, 21.0, 22.0])
    lon, lat = np.meshgrid(lon1d, lat1d)
    depth = np.full((3, 3), -50.0)
    mask = np.ones((3, 3), dtype=int)

    data = {"lon": lon, "lat": lat, "depth": depth, "mask": mask}
    out_file = str(tmp_path / "test_no_orog.jpg")

    fig = plot_grid(data, title="Purely Underwater Grid", output_path=out_file, max_orography=10.0)
    assert fig is not None
    texts = [t.get_text() for ax in fig.axes for t in ax.texts]
    assert "Grid contains no orography" in texts


def test_vis_ugrid(tmp_path):
    lon1d = np.array([10.0, 11.0, 12.0])
    lat1d = np.array([20.0, 21.0, 22.0])
    lon, lat = np.meshgrid(lon1d, lat1d)
    depth = np.array([[-10.0, -20.0, -30.0], [-15.0, -25.0, -35.0], [-10.0, -10.0, -10.0]])
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




def test_plot_grid_script_missing_input_file(tmp_path: Path):
    """Verify plot_grid.sh error reporting when specified input dataset file does not exist."""
    repo_root = Path(__file__).parent.parent
    script_path = repo_root / "plot_grid.sh"
    non_existent_nc = tmp_path / "non_existent_grid.nc"

    result = subprocess.run(
        [str(script_path), "-i", str(non_existent_nc)],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode != 0
    assert "Error: Input grid dataset file or prefix" in result.stderr
    assert "./run_gridgen.sh" in result.stderr




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


def test_plot_grid_show_in_headless_env(tmp_path: Path):
    """Verify plot_grid with show=True in headless environment skips show without UserWarning."""
    lon1d = np.array([10.0, 11.0, 12.0])
    lat1d = np.array([20.0, 21.0, 22.0])
    lon, lat = np.meshgrid(lon1d, lat1d)
    data = {
        "lon": lon,
        "lat": lat,
        "depth": np.full((3, 3), 10.0),
        "mask": np.ones((3, 3), dtype=int),
    }

    out_file = str(tmp_path / "test_show_headless.jpg")
    fig = plot_grid(data, output_path=out_file, show=True)
    assert fig is not None
    assert os.path.exists(out_file)


def test_plot_grid_script_no_canvas_warning(tmp_path: Path):
    """Verify plot_grid.sh runs without UserWarning when called with --display in headless environment."""
    repo_root = Path(__file__).parent.parent
    script_path = repo_root / "plot_grid.sh"

    lon1d = np.array([10.0, 11.0, 12.0])
    lat1d = np.array([20.0, 21.0, 22.0])
    lon, lat = np.meshgrid(lon1d, lat1d)
    depth = np.full((3, 3), 10.0)
    mask = np.ones((3, 3), dtype=int)
    ds = create_ugrid_dataset(lon, lat, depth, mask, title="Warning Test")

    nc_file = tmp_path / "warning_test_ugrid.nc"
    write_ugrid_nc(ds, str(nc_file))

    out_jpg = tmp_path / "warning_test.jpg"

    result = subprocess.run(
        [
            str(script_path),
            "-i",
            str(nc_file),
            "-o",
            str(out_jpg),
            "-f",
            "jpg",
            "--display",
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    assert "FigureCanvasAgg is non-interactive" not in result.stderr
    assert "UserWarning" not in result.stderr




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


def test_default_title_and_subtitle(tmp_path):
    """Verify default title and subtitle are applied when not overridden."""
    lon1d = np.array([10.0, 20.0])
    lat1d = np.array([10.0, 18.0])
    lon, lat = np.meshgrid(lon1d, lat1d)
    data = {"lon": lon, "lat": lat, "depth": np.full((2, 2), -10.0), "mask": np.ones((2, 2), dtype=int)}

    fig = plot_grid(data)
    ax = fig.axes[0]
    assert fig._suptitle is not None
    assert fig._suptitle.get_text() == "WAVEWATCH IV Grid"
    assert ax.get_title() == "Bathymetry and Orography"


def test_custom_and_disabled_title_subtitle(tmp_path):
    """Verify custom titles/subtitles and disabled titles/subtitles."""
    lon1d = np.array([10.0, 20.0])
    lat1d = np.array([10.0, 18.0])
    lon, lat = np.meshgrid(lon1d, lat1d)
    data = {"lon": lon, "lat": lat, "depth": np.full((2, 2), -10.0), "mask": np.ones((2, 2), dtype=int)}

    # Custom
    fig = plot_grid(data, title="Custom Main Title", subtitle="Custom Subtitle")
    ax = fig.axes[0]
    assert fig._suptitle.get_text() == "Custom Main Title"
    assert ax.get_title() == "Custom Subtitle"

    # Disabled
    fig_no_title = plot_grid(data, title=None, subtitle=None)
    ax_no_title = fig_no_title.axes[0]
    assert fig_no_title._suptitle is None or fig_no_title._suptitle.get_text() == ""
    assert ax_no_title.get_title() == ""


def test_zoom_functionality(tmp_path):
    """Verify zoom shifts view box with factor 1 and narrows view box with factor 2."""
    lon1d = np.array([10.0, 20.0])  # span_lon = 10
    lat1d = np.array([10.0, 18.0])  # span_lat = 8
    lon, lat = np.meshgrid(lon1d, lat1d)
    data = {"lon": lon, "lat": lat, "depth": np.full((2, 2), -10.0), "mask": np.ones((2, 2), dtype=int)}

    # Zoom factor 1 centered at (15.0, 14.0) -> same span [10, 20], [10, 18]
    fig1 = plot_grid(data, zoom=(15.0, 14.0, 1.0))
    ax1 = fig1.axes[0]
    assert ax1.get_xlim() == (10.0, 20.0)
    assert ax1.get_ylim() == (10.0, 18.0)

    # Zoom factor 1 shifted to central lon 18.0, lat 14.0 -> xlim=[13.0, 23.0]
    fig_shift = plot_grid(data, zoom=(18.0, 14.0, 1.0))
    ax_shift = fig_shift.axes[0]
    assert ax_shift.get_xlim() == (13.0, 23.0)
    assert ax_shift.get_ylim() == (10.0, 18.0)

    # Zoom factor 2 centered at (15.0, 14.0) -> half span [12.5, 17.5], [12.0, 16.0]
    fig2 = plot_grid(data, zoom=(15.0, 14.0, 2.0))
    ax2 = fig2.axes[0]
    assert ax2.get_xlim() == (12.5, 17.5)
    assert ax2.get_ylim() == (12.0, 16.0)


def test_zoom_cli_options(tmp_path: Path):
    """Verify --zoom and --no-title / --no-subtitle / --no-mask CLI options via plot_grid.sh."""
    repo_root = Path(__file__).parent.parent
    script_path = repo_root / "plot_grid.sh"

    lon1d = np.array([10.0, 20.0])
    lat1d = np.array([10.0, 18.0])
    lon, lat = np.meshgrid(lon1d, lat1d)
    depth = np.full((2, 2), -10.0)
    mask = np.ones((2, 2), dtype=int)
    ds = create_ugrid_dataset(lon, lat, depth, mask, title="CLI Options Test")

    nc_file = tmp_path / "cli_test_ugrid.nc"
    write_ugrid_nc(ds, str(nc_file))
    out_jpg = tmp_path / "cli_test.jpg"

    result = subprocess.run(
        [
            str(script_path),
            "-i",
            str(nc_file),
            "-o",
            str(out_jpg),
            "-f",
            "jpg",
            "--no-title",
            "--no-subtitle",
            "--no-mask",
            "--zoom",
            "15.0",
            "14.0",
            "2.0",
            "--no-display",
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    assert out_jpg.exists()


def test_mask_option_removed(tmp_path: Path):
    """Verify passing --mask raises an error as --mask option is removed."""
    repo_root = Path(__file__).parent.parent
    script_path = repo_root / "plot_grid.sh"

    nc_file = tmp_path / "dummy_ugrid.nc"
    lon, lat = np.meshgrid([10, 11], [10, 11])
    ds = create_ugrid_dataset(lon, lat, np.full((2, 2), -10.0), np.ones((2, 2), dtype=int))
    write_ugrid_nc(ds, str(nc_file))

    result = subprocess.run(
        [
            str(script_path),
            "-i",
            str(nc_file),
            "--mask",
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode != 0
    assert "unrecognized option '--mask'" in result.stderr or "Unknown option: --mask" in result.stderr
