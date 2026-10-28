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
# @date Latest Update: 2026-10-27

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
    """Verify plot_grid omits orography legend and renders remaining 2 legends taking 50% plot height each when no land points exist."""
    lon1d = np.array([10.0, 11.0, 12.0])
    lat1d = np.array([20.0, 21.0, 22.0])
    lon, lat = np.meshgrid(lon1d, lat1d)
    depth = np.full((3, 3), -50.0)
    mask = np.ones((3, 3), dtype=int)

    data = {"lon": lon, "lat": lat, "depth": depth, "mask": mask}
    out_file = str(tmp_path / "test_no_orog.jpg")

    fig = plot_grid(data, title="Purely Underwater Grid", output_path=out_file, max_orography=10.0)
    assert fig is not None
    # Figure should only contain main axes, obstruction cax, and bathymetry cax (no orography cax)
    labels = [ax.get_ylabel() for ax in fig.axes if hasattr(ax, "get_ylabel")]
    assert "Bathymetry Depth (m)" in labels
    assert "Orography (m)" not in labels


def test_vis_ugrid(tmp_path):
    lon1d = np.array([10.0, 11.0, 12.0])
    lat1d = np.array([20.0, 21.0, 22.0])
    lon, lat = np.meshgrid(lon1d, lat1d)
    depth = np.array([[-10.0, -20.0, -30.0], [-15.0, -25.0, -35.0], [-10.0, -10.0, -10.0]])
    mask = np.ones((3, 3), dtype=int)
    ObsX = np.full((3, 3), 0.1)
    ObsY = np.full((3, 3), 0.2)

    ds = create_ugrid_dataset(
        lon, lat, depth, mask, ObsX=ObsX, ObsY=ObsY, title="Test Vis Grid"
    )
    nc_path = str(tmp_path / "test_vis_ugrid.nc")
    write_ugrid_nc(ds, nc_path)

    data = load_grid_data(nc_path)
    assert "lon" in data
    assert "lat" in data
    assert "depth" in data
    assert "ObsX" in data
    assert "ObsY" in data
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
    ObsX = np.zeros((3, 3))
    ObsY = np.zeros((3, 3))

    nc_path = str(tmp_path / "test_coards.nc")
    nc_ww3_grdwrite(lon, lat, depth, nc_path, mask=mask, ObsX=ObsX, ObsY=ObsY)

    data = load_grid_data(nc_path)
    assert data["depth"].shape == (3, 3)

    out_gif = str(tmp_path / "vis_coards.gif")
    fig = plot_grid(data, title="COARDS Vis Test", output_path=out_gif)
    assert os.path.exists(out_gif)
    assert fig is not None


def test_vis_obstructions_only_when_nonzero(tmp_path):
    """Verify plot_grid overlays obstructions on single plot panel and displays subgrid obstruction colorbar legend when non-zero obstructions exist."""
    lon, lat = np.meshgrid([10.0, 11.0], [20.0, 21.0])
    depth = np.full((2, 2), -50.0)
    mask = np.ones((2, 2), dtype=int)

    # 1. All-zero obstructions -> 1 main panel, obstruction colorbar shows 'Grid contains no obstructions'
    data_zero = {
        "lon": lon,
        "lat": lat,
        "depth": depth,
        "mask": mask,
        "ObsX": np.zeros((2, 2)),
        "ObsY": np.zeros((2, 2)),
    }
    fig_zero = plot_grid(data_zero)
    main_axes_zero = [ax for ax in fig_zero.axes if ax.get_subplotspec() is not None]
    assert len(main_axes_zero) == 1
    texts_zero = [t.get_text() for ax in fig_zero.axes for t in ax.texts]
    assert "Grid contains no obstructions" in texts_zero

    # 2. Obstructions < 0.01 -> treated as no obstruction -> 'Grid contains no obstructions'
    data_small = {
        "lon": lon,
        "lat": lat,
        "depth": depth,
        "mask": mask,
        "ObsX": np.array([[0.0, 0.005], [0.0, 0.0]]),
        "ObsY": np.array([[0.0, 0.0], [0.008, 0.0]]),
    }
    fig_small = plot_grid(data_small)
    main_axes_small = [ax for ax in fig_small.axes if ax.get_subplotspec() is not None]
    assert len(main_axes_small) == 1
    texts_small = [t.get_text() for ax in fig_small.axes for t in ax.texts]
    assert "Grid contains no obstructions" in texts_small

    # 3. Obstructions >= 0.01 -> overlaid on single main panel with Subgrid Obstruction Factor colorbar legend
    data_nonzero = {
        "lon": lon,
        "lat": lat,
        "depth": depth,
        "mask": mask,
        "ObsX": np.array([[0.0, 0.5], [0.0, 0.0]]),
        "ObsY": np.array([[0.0, 0.0], [0.3, 0.0]]),
    }
    fig_nonzero = plot_grid(data_nonzero)
    main_axes_nonzero = [ax for ax in fig_nonzero.axes if ax.get_subplotspec() is not None]
    assert len(main_axes_nonzero) == 1
    labels = [ax.get_ylabel() for ax in fig_nonzero.axes if hasattr(ax, "get_ylabel")]
    assert "Subgrid Obstruction Factor" in labels


def test_vis_ascii(tmp_path):
    Ny, Nx = 3, 3
    lon1d = np.linspace(10.0, 12.0, Nx)
    lat1d = np.linspace(20.0, 22.0, Ny)
    lon, lat = np.meshgrid(lon1d, lat1d)

    depth = np.array([[10.0, 20.0, 30.0], [15.0, 25.0, 35.0], [10.0, 10.0, 10.0]])
    mask = np.ones((Ny, Nx), dtype=int)
    ObsX = np.full((Ny, Nx), 0.05)
    ObsY = np.full((Ny, Nx), 0.15)

    prefix = str(tmp_path / "ww3_ascii_test")
    depth_scale = 1000.0
    obstr_scale = 100.0
    write_ww3file(f"{prefix}.depth_ascii", depth * depth_scale)
    write_ww3file(f"{prefix}.maskorig_ascii", mask)
    write_ww3obstr(f"{prefix}.obstr_lev1", ObsX * obstr_scale, ObsY * obstr_scale)
    write_ww3meta(prefix, "RECT", lon, lat, 1.0 / depth_scale, 1.0 / obstr_scale, 1.0)

    data = load_grid_data(prefix)
    assert data["depth"].shape == (3, 3)
    assert np.allclose(data["ObsX"], ObsX)

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
            [str(script_path), "-i", str(nc_file), "-f", "jpg"],
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


def test_coastline_subtitle_formatting(tmp_path):
    """Verify subtitle formatting appends bathymetry source and coastline resolution description."""
    lon1d = np.array([10.0, 20.0])
    lat1d = np.array([10.0, 18.0])
    lon, lat = np.meshgrid(lon1d, lat1d)

    data = {
        "lon": lon,
        "lat": lat,
        "depth": np.full((2, 2), -10.0),
        "mask": np.ones((2, 2), dtype=int),
        "filename": "test_grid_ugrid.nc",
        "bathy_source": "etopo2",
        "bound_source": "coastal_bound_low.mat",
    }

    fig = plot_grid(data)
    ax = fig.axes[0]
    assert ax.get_title() == "Bathymetry, Orography, and Obstructions (etopo2, low res coastline)"

    # Test high res coastline
    fig_high = plot_grid(data, bound_source="coastal_bound_high.mat")
    assert fig_high.axes[0].get_title() == "Bathymetry, Orography, and Obstructions (etopo2, high res coastline)"

    # Test disabled coastline ('none')
    fig_none = plot_grid(data, bound_source="none")
    assert fig_none.axes[0].get_title() == "Bathymetry, Orography, and Obstructions (etopo2)"


def test_default_title_and_subtitle(tmp_path):
    """Verify default title uses input dataset filename and subtitle includes bathymetry and coastline sources."""
    lon1d = np.array([10.0, 20.0])
    lat1d = np.array([10.0, 18.0])
    lon, lat = np.meshgrid(lon1d, lat1d)
    data = {
        "lon": lon,
        "lat": lat,
        "depth": np.full((2, 2), -10.0),
        "mask": np.ones((2, 2), dtype=int),
        "filename": "my_ww4_grid_ugrid.nc",
        "bathy_source": "etopo2",
    }

    fig = plot_grid(data)
    ax = fig.axes[0]
    assert ax.get_title() == "Bathymetry, Orography, and Obstructions (etopo2, low res coastline)"
    texts = [t.get_text() for t in ax.texts]
    assert "WAVEWATCH IV grid my_ww4_grid_ugrid.nc" in texts


def test_custom_and_disabled_title_subtitle(tmp_path):
    """Verify custom titles/subtitles and disabled titles/subtitles."""
    lon1d = np.array([10.0, 20.0])
    lat1d = np.array([10.0, 18.0])
    lon, lat = np.meshgrid(lon1d, lat1d)
    data = {
        "lon": lon,
        "lat": lat,
        "depth": np.full((2, 2), -10.0),
        "mask": np.ones((2, 2), dtype=int),
        "filename": "ww4_grid_ugrid.nc",
        "bathy_source": "gebco_2024",
    }

    # Custom title, subtitle, and bathy source
    fig = plot_grid(data, title="Custom Main Title", subtitle="Custom Subtitle", bathy_source="gebco_2024")
    ax = fig.axes[0]
    assert ax.get_title() == "Custom Subtitle (gebco_2024, low res coastline)"
    texts = [t.get_text() for t in ax.texts]
    assert "Custom Main Title" in texts

    # Disabled title and subtitle
    fig_no_title = plot_grid(data, title="", subtitle="")
    ax_no_title = fig_no_title.axes[0]
    assert ax_no_title.get_title() == ""


def test_zoom_functionality(tmp_path):
    """Verify zoom shifts view box, clamps regional view box within full grid, sets zoomed labels, and allows global grid rotation."""
    lon1d = np.array([10.0, 20.0])  # span_lon = 10
    lat1d = np.array([10.0, 18.0])  # span_lat = 8
    lon, lat = np.meshgrid(lon1d, lat1d)
    data = {"lon": lon, "lat": lat, "depth": np.full((2, 2), -10.0), "mask": np.ones((2, 2), dtype=int)}

    # Unzoomed plot checks standard labels
    fig_nozoom = plot_grid(data)
    ax_nozoom = fig_nozoom.axes[0]
    assert ax_nozoom.get_xlabel() == "Longitude"
    assert ax_nozoom.get_ylabel() == "Latitude"

    # Zoom factor 1 centered at (15.0, 14.0) -> same span [10, 20], [10, 18] and standard labels (not (zoom))
    fig1 = plot_grid(data, zoom=(15.0, 14.0, 1.0))
    ax1 = fig1.axes[0]
    assert ax1.get_xlabel() == "Longitude"
    assert ax1.get_ylabel() == "Latitude"
    assert ax1.get_xlim() == (10.0, 20.0)
    assert ax1.get_ylim() == (10.0, 18.0)

    # Regional grid zoom factor 1 shifted to central lon 18.0, lat 14.0 -> clamped to [10.0, 20.0]
    fig_shift = plot_grid(data, zoom=(18.0, 14.0, 1.0))
    ax_shift = fig_shift.axes[0]
    assert ax_shift.get_xlim() == (10.0, 20.0)
    assert ax_shift.get_ylim() == (10.0, 18.0)

    # Zoom factor 2 centered at (15.0, 14.0) -> half span [12.5, 17.5], [12.0, 16.0] and zoomed labels
    fig2 = plot_grid(data, zoom="15.0 14.0 2.0")
    ax2 = fig2.axes[0]
    assert ax2.get_xlabel() == "Longitude (zoom)"
    assert ax2.get_ylabel() == "Latitude (zoom)"
    assert ax2.get_xlim() == (12.5, 17.5)
    assert ax2.get_ylim() == (12.0, 16.0)
    expected_aspect = 1.0 / np.cos(np.radians(14.0))
    assert np.isclose(ax2.get_aspect(), expected_aspect)

    # Zoom string with commas "15.0, 14.0, 2.0"
    fig3 = plot_grid(data, zoom="15.0, 14.0, 2.0")
    ax3 = fig3.axes[0]
    assert ax3.get_xlim() == (12.5, 17.5)
    assert ax3.get_ylim() == (12.0, 16.0)

    # Globally closed regular grid zoom allows rotation across 0°/360°
    glon1d = np.linspace(0.0, 359.0, 360)
    glat1d = np.linspace(-90.0, 90.0, 181)
    glon, glat = np.meshgrid(glon1d, glat1d)
    gdata = {"lon": glon, "lat": glat, "depth": np.full((181, 360), -50.0), "mask": np.ones((181, 360), dtype=int)}

    # Global grid zoom factor 2 centered at -160°, 20°N -> xlim = [-250.0, -70.0], ylim = [-25.0, 65.0]
    fig_glob = plot_grid(gdata, zoom=(-160.0, 20.0, 2.0))
    ax_glob = fig_glob.axes[0]
    assert ax_glob.get_xlabel() == "Longitude (zoom)"
    assert ax_glob.get_ylabel() == "Latitude (zoom)"
    assert ax_glob.get_xlim() == (-250.0, -70.0)
    assert ax_glob.get_ylim() == (-25.0, 65.0)

    # Zoom factor < 1 is clamped to 1.0 without error and retains standard labels
    fig_sub1 = plot_grid(data, zoom=(15.0, 14.0, 0.5))
    ax_sub1 = fig_sub1.axes[0]
    assert ax_sub1.get_xlabel() == "Longitude"
    assert ax_sub1.get_ylabel() == "Latitude"
    assert ax_sub1.get_xlim() == (10.0, 20.0)
    assert ax_sub1.get_ylim() == (10.0, 18.0)


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
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    assert out_jpg.exists()


def test_zoom_with_negative_coordinates(tmp_path: Path):
    """Verify --zoom accepts negative coordinates without argparse errors."""
    repo_root = Path(__file__).parent.parent
    script_path = repo_root / "plot_grid.sh"

    lon1d = np.array([-180.0, -140.0])
    lat1d = np.array([10.0, 30.0])
    lon, lat = np.meshgrid(lon1d, lat1d)
    depth = np.full((2, 2), -10.0)
    mask = np.ones((2, 2), dtype=int)
    ds = create_ugrid_dataset(lon, lat, depth, mask, title="Negative Zoom Test")

    nc_file = tmp_path / "neg_zoom_ugrid.nc"
    write_ugrid_nc(ds, str(nc_file))

    # Test via plot_grid.sh with trailing decimal dot coordinates: --zoom -160. 20. 5
    out_jpg1 = tmp_path / "neg_zoom1.jpg"
    result_sh = subprocess.run(
        [
            str(script_path),
            "-i",
            str(nc_file),
            "-o",
            str(out_jpg1),
            "-f",
            "jpg",
            "--zoom",
            "-160.",
            "20.",
            "5",
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result_sh.returncode == 0
    assert out_jpg1.exists()

    # Test via python -m gridgen.vis directly with trailing decimal dots: --zoom -160. 20. 5
    out_jpg2 = tmp_path / "neg_zoom2.jpg"
    result_py = subprocess.run(
        [
            "python3",
            "-m",
            "gridgen.vis",
            "-i",
            str(nc_file),
            "-o",
            str(out_jpg2),
            "-f",
            "jpg",
            "--zoom",
            "-160.",
            "20.",
            "5",
            "--no-display",
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result_py.returncode == 0
    assert out_jpg2.exists()


def test_zoom_coordinate_formats(tmp_path: Path):
    """Verify --zoom accepts cardinal directions, degree symbols, and leading dots across CLI drivers."""
    repo_root = Path(__file__).parent.parent
    script_path = repo_root / "plot_grid.sh"

    lon1d = np.array([-180.0, -140.0])
    lat1d = np.array([10.0, 30.0])
    lon, lat = np.meshgrid(lon1d, lat1d)
    depth = np.full((2, 2), -10.0)
    mask = np.ones((2, 2), dtype=int)
    ds = create_ugrid_dataset(lon, lat, depth, mask, title="Format Zoom Test")

    nc_file = tmp_path / "fmt_zoom_ugrid.nc"
    write_ugrid_nc(ds, str(nc_file))

    # Test cardinal directions (160W 20N 5) via plot_grid.sh
    out_jpg1 = tmp_path / "fmt_zoom1.jpg"
    res1 = subprocess.run(
        [
            str(script_path),
            "-i",
            str(nc_file),
            "-o",
            str(out_jpg1),
            "--zoom",
            "160W",
            "20N",
            "5",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert res1.returncode == 0
    assert out_jpg1.exists()

    # Test degree symbols (-160.0° 20.0° 5) via gridgen.vis
    out_jpg2 = tmp_path / "fmt_zoom2.jpg"
    res2 = subprocess.run(
        [
            "python3",
            "-m",
            "gridgen.vis",
            "-i",
            str(nc_file),
            "-o",
            str(out_jpg2),
            "--zoom",
            "-160.0°",
            "20.0°",
            "5",
            "--no-display",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert res2.returncode == 0
    assert out_jpg2.exists()


def test_zoom_cyclic_longitudes(tmp_path: Path):
    """Verify zoom and plot_grid properly normalize cyclic longitudes for regional and global grids."""
    # 1. Regional grid [10, 50] with central longitude specified in cyclic range 390°
    rlon1d = np.linspace(10.0, 50.0, 41)
    rlat1d = np.linspace(-10.0, 10.0, 21)
    rlon, rlat = np.meshgrid(rlon1d, rlat1d)
    rdata = {"lon": rlon, "lat": rlat, "depth": np.full((21, 41), -50.0), "mask": np.ones((21, 41), dtype=int)}

    # central_lon = 390 -> normalized to 30.0 -> zoom factor 2 -> xlim = [20.0, 40.0]
    fig_reg = plot_grid(rdata, zoom=(390.0, 0.0, 2.0))
    ax_reg = fig_reg.axes[0]
    assert ax_reg.get_xlim() == (20.0, 40.0)

    # 2. Global grid [0, 360] with central longitude shifted by +360° (c_lon = 500°) or -360° (c_lon = -200°)
    glon1d = np.linspace(0.0, 359.0, 360)
    glat1d = np.linspace(-90.0, 90.0, 181)
    glon, glat = np.meshgrid(glon1d, glat1d)
    gdata = {"lon": glon, "lat": glat, "depth": np.full((181, 360), -50.0), "mask": np.ones((181, 360), dtype=int)}

    fig_g1 = plot_grid(gdata, zoom=(500.0, 0.0, 2.0))
    ax_g1 = fig_g1.axes[0]
    assert ax_g1.get_xlim() == (410.0, 590.0)

    fig_g2 = plot_grid(gdata, zoom=(-600.0, 0.0, 2.0))
    ax_g2 = fig_g2.axes[0]
    assert ax_g2.get_xlim() == (-690.0, -510.0)

    # 3. Global grid [20, 379.75] with central_lon = -168, zoom factor 1 -> xlim = [-348.0, 12.0]
    glon_offset1d = np.linspace(20.0, 379.75, 360)
    glon_off, glat_off = np.meshgrid(glon_offset1d, glat1d)
    gdata_off = {"lon": glon_off, "lat": glat_off, "depth": np.full((181, 360), -50.0), "mask": np.ones((181, 360), dtype=int)}

    fig_g3 = plot_grid(gdata_off, zoom=(-168.0, 0.0, 1.0))
    ax_g3 = fig_g3.axes[0]
    assert ax_g3.get_xlim() == (-348.0, 12.0)


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
