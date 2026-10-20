# WAVEWATCH III (WW3) / WAVEWATCH IV (WW4) Gridgen Package
#
# Copyright 2026 National Weather Service (NWS), NOAA. All rights reserved.
# NWS often uses Generative AI (GenAI) for code development and refactoring.
# Whenever GenAI is used, NWS requires a full human review of code before it
# is added to its repositories.
#
# @file vis.py
# @brief Visualization utility for WAVEWATCH III / WAVEWATCH IV grid and obstructions.
# @author Aldgisl (Agentic AI), Hendrik Tolman
# @author Jules (Agentic AI) (contributor)
# @date Initial: 2026-10-05
# @date Latest Update: 2026-10-20
#
# Code Heritage:
# WAVEWATCH III (WW3) / WAVEWATCH IV (WW4) Grid and Obstruction Visualization module.

"""Visualization utility for WAVEWATCH III (WW3) / WAVEWATCH IV (WW4) grid and obstructions."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import xarray as xr

from .io.ascii import read_ww3file, read_ww3meta, read_ww3obstr


def extract_grid_name(filepath: str | Path) -> str:
    """Extract grid prefix identifier from input filepath.

    Parameters
    ----------
    filepath : str or Path
        Input grid file path or prefix.

    Returns
    -------
    str
        Grid prefix identifier (e.g. 'ww4_grid').
    """
    path = Path(filepath)
    fname = path.name
    suffixes = [
        "_ugrid.nc",
        "_coards.nc",
        ".depth_ascii",
        ".maskorig_ascii",
        ".obstr_lev1",
        ".meta",
        ".nc",
    ]
    for s in suffixes:
        if fname.endswith(s):
            return fname[: -len(s)]
    return path.stem or "ww4_grid"


def load_grid_data(filepath: str | Path) -> dict[str, Any]:
    """Load WAVEWATCH grid, bathymetry, mask, and obstruction data from a dataset file or ASCII grid prefix.

    Parameters
    ----------
    filepath : str or Path
        Path to NetCDF UGRID (_ugrid.nc), NetCDF COARDS (_coards.nc),
        ASCII file (.depth_ascii), or grid prefix identifier.

    Returns
    -------
    dict[str, Any]
        Dictionary containing 'lon', 'lat', 'depth', 'mask', 'sx', and 'sy' 2D numpy arrays.
    """
    path = Path(filepath)

    # 1. NetCDF format
    if path.suffix == ".nc":
        ds = xr.open_dataset(path)

        # 2D Grid format (WW4 NetCDF-UGRID or COARDS with 2D grid variables)
        if "grid_lon" in ds and "grid_lat" in ds:
            lon = ds["grid_lon"].values
            lat = ds["grid_lat"].values
            depth = ds["grid_depth"].values if "grid_depth" in ds else (ds["depth"].values if "depth" in ds else np.zeros_like(lon))
            mask = ds["grid_mask"].values if "grid_mask" in ds else (ds["mask"].values if "mask" in ds else np.ones_like(lon))
            sx = ds["grid_sx"].values if "grid_sx" in ds else (ds["sx"].values if "sx" in ds else None)
            sy = ds["grid_sy"].values if "grid_sy" in ds else (ds["sy"].values if "sy" in ds else None)

        # UGRID 1.0 format fallback
        elif "face_lon" in ds and "face_lat" in ds:
            face_lon = ds["face_lon"].values
            face_lat = ds["face_lat"].values
            depth_raw = ds["depth"].values if "depth" in ds else np.zeros_like(face_lon)
            mask_raw = ds["mask"].values if "mask" in ds else np.ones_like(face_lon)
            sx_raw = ds["sx"].values if "sx" in ds else None
            sy_raw = ds["sy"].values if "sy" in ds else None

            # Attempt to reconstruct 2D grid structure
            unique_lons = np.unique(face_lon)
            unique_lats = np.unique(face_lat)
            Nx = len(unique_lons)
            Ny = len(unique_lats)

            if Nx * Ny == len(face_lon):
                lon = face_lon.reshape(Ny, Nx)
                lat = face_lat.reshape(Ny, Nx)
                depth = depth_raw.reshape(Ny, Nx)
                mask = mask_raw.reshape(Ny, Nx)
                sx = sx_raw.reshape(Ny, Nx) if sx_raw is not None else None
                sy = sy_raw.reshape(Ny, Nx) if sy_raw is not None else None
            else:
                lon = face_lon
                lat = face_lat
                depth = depth_raw
                mask = mask_raw
                sx = sx_raw
                sy = sy_raw

        # COARDS NetCDF format
        elif "lon" in ds and "lat" in ds:
            lon1d = ds["lon"].values
            lat1d = ds["lat"].values
            if lon1d.ndim == 1 and lat1d.ndim == 1:
                lon, lat = np.meshgrid(lon1d, lat1d)
            else:
                lon, lat = lon1d, lat1d

            depth = ds["z"].values if "z" in ds else np.zeros_like(lon)
            mask = ds["mask"].values if "mask" in ds else np.ones_like(lon)
            sx = ds["sx"].values if "sx" in ds else None
            sy = ds["sy"].values if "sy" in ds else None

        ds.close()
        return {
            "lon": lon,
            "lat": lat,
            "depth": depth,
            "mask": mask,
            "sx": sx,
            "sy": sy,
        }

    # 2. Legacy WW3 ASCII files
    base_prefix = str(path).replace(".depth_ascii", "").replace(".maskorig_ascii", "")
    meta_file = f"{base_prefix}.meta"
    depth_file = f"{base_prefix}.depth_ascii"
    mask_file = f"{base_prefix}.maskorig_ascii"
    obstr_file = f"{base_prefix}.obstr_lev1"

    if Path(meta_file).exists():
        _, lon, lat, depth_scale, obstr_scale, _ = read_ww3meta(meta_file)
        Ny, Nx = lon.shape

        depth = (
            read_ww3file(depth_file, Ny, Nx) * depth_scale
            if Path(depth_file).exists()
            else np.zeros((Ny, Nx))
        )
        mask = (
            read_ww3file(mask_file, Ny, Nx)
            if Path(mask_file).exists()
            else np.ones((Ny, Nx), dtype=int)
        )

        if Path(obstr_file).exists():
            sx_raw, sy_raw = read_ww3obstr(obstr_file, Ny, Nx)
            sx = sx_raw * obstr_scale
            sy = sy_raw * obstr_scale
        else:
            sx, sy = None, None

        return {
            "lon": lon,
            "lat": lat,
            "depth": depth,
            "mask": mask,
            "sx": sx,
            "sy": sy,
        }

    raise FileNotFoundError(
        f"Could not load grid data from path or prefix '{filepath}'"
    )


def plot_grid(
    data: dict[str, Any],
    title: str = "WAVEWATCH IV Grid",
    output_path: str | Path | None = None,
    show: bool = False,
    show_mask: bool = True,
    max_depth: float | None = -2500.0,
    max_orography: float | None = 10.0,
) -> matplotlib.figure.Figure:
    """Graphically display resulting grid bathymetry and orography plot.

    Parameters
    ----------
    data : dict[str, Any]
        Dictionary containing grid data ('lon', 'lat', 'depth', 'mask', 'sx', 'sy').
    title : str
        Main figure title string.
    output_path : str or Path, optional
        File path where the resulting plot figure should be saved.
    show : bool
        If True, call matplotlib plt.show() to display interactively.
    show_mask : bool
        If True, mask out dry land cells (mask == 0) and use dark green background. Default is True.
    max_depth : float, optional
        Maximum depth (minimum numerical bathymetry limit, e.g., -2500.0) for color scale range limit. Default is -2500.0.
    max_orography : float, optional
        Maximum orography elevation limit in meters (default: 10.0) for land color scale.

    Returns
    -------
    matplotlib.figure.Figure
        Created Matplotlib figure object.
    """
    lon = data["lon"]
    lat = data["lat"]
    depth = data["depth"].copy()
    mask = data["mask"]

    fig, ax1 = plt.subplots(figsize=(8, 5))

    dark_green = "#1b4332"  # Dark green background for land/sea mask
    if show_mask:
        ax1.set_facecolor(dark_green)

    # Separate underwater bathymetry (depth <= 0) and land orography (depth > 0)
    bathymetry_mask = (depth <= 0) & (mask != 0) if show_mask else (depth <= 0)
    orography_mask = (depth > 0) & (depth < 999999.0) & (mask != 0) if show_mask else ((depth > 0) & (depth < 999999.0))

    depth_bathy = np.where(bathymetry_mask, depth, np.nan)
    depth_orog = np.where(orography_mask, np.clip(depth, 0.0, max_orography if max_orography is not None else 10.0), np.nan)

    vmin_bathy = max_depth if max_depth is not None else None
    vmax_bathy = 0.0 if max_depth is not None else None

    vmax_orog = max_orography if max_orography is not None else 10.0

    if lon.ndim == 2:
        pcm1 = ax1.pcolormesh(
            lon, lat, depth_bathy, cmap="Blues_r", vmin=vmin_bathy, vmax=vmax_bathy, shading="nearest"
        )
        if np.any(~np.isnan(depth_orog)):
            pcm2 = ax1.pcolormesh(
                lon, lat, depth_orog, cmap="YlOrBr", vmin=0.0, vmax=vmax_orog, shading="nearest"
            )
            fig.colorbar(pcm2, ax=ax1, label="Orography (m)")
    else:
        pcm1 = ax1.scatter(lon, lat, c=depth_bathy, cmap="Blues_r", vmin=vmin_bathy, vmax=vmax_bathy)
        if np.any(~np.isnan(depth_orog)):
            pcm2 = ax1.scatter(lon, lat, c=depth_orog, cmap="YlOrBr", vmin=0.0, vmax=vmax_orog)
            fig.colorbar(pcm2, ax=ax1, label="Orography (m)")

    fig.colorbar(pcm1, ax=ax1, label="Bathymetry Depth (m)")
    ax1.set_title("Bathymetry & Orography")
    ax1.set_xlabel("Longitude (°E)")
    ax1.set_ylabel("Latitude (°N)")
    ax1.grid(True, linestyle="--", alpha=0.5)

    fig.suptitle(title, fontsize=14, fontweight="bold")
    fig.tight_layout()

    if output_path is not None:
        out_p = Path(output_path)
        if out_p.suffix.lower() in (".gif", ".giff"):
            import io

            from PIL import Image

            buf = io.BytesIO()
            fig.savefig(buf, format="png", dpi=300, bbox_inches="tight")
            buf.seek(0)
            img = Image.open(buf)
            img.save(out_p, format="GIF")
        else:
            fig.savefig(output_path, dpi=300, bbox_inches="tight")
        print(f"Saved grid plot to '{output_path}'")

    if show:
        import os

        display_env = os.environ.get("DISPLAY")
        wayland_env = os.environ.get("WAYLAND_DISPLAY")
        backend = matplotlib.get_backend().lower()
        canvas_type = type(fig.canvas).__name__
        non_interactive_backends = {"agg", "pdf", "ps", "svg", "cairo", "template"}

        if (
            (display_env or wayland_env)
            and backend not in non_interactive_backends
            and canvas_type != "FigureCanvasAgg"
        ):
            plt.show()
        else:
            print(
                "Skipping interactive figure display (no active display server or non-interactive Matplotlib backend)."
            )

    return fig


def main() -> None:
    """CLI driver for displaying resulting grid bathymetry."""
    parser = argparse.ArgumentParser(
        description="Graphically display WAVEWATCH III / IV resulting grid."
    )
    parser.add_argument(
        "-i",
        "--input",
        type=str,
        default="ww4_grid_ugrid.nc",
        help="Input dataset filepath (_ugrid.nc, _coards.nc, or ASCII prefix)",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=str,
        default=None,
        help="Output image file path (default: <GRIDNAME>.<format>)",
    )
    parser.add_argument(
        "-f",
        "--format",
        type=str,
        default="jpg",
        choices=["jpg", "jpeg", "png", "pdf", "eps", "gif"],
        help="Output graphic format: jpg, png, pdf, eps, or gif (default: jpg)",
    )
    parser.add_argument(
        "--title",
        type=str,
        default="WAVEWATCH IV Grid",
        help="Figure title",
    )
    parser.add_argument(
        "--mask",
        dest="mask",
        action="store_true",
        default=True,
        help="Apply land-sea mask to dry cells (default: enabled)",
    )
    parser.add_argument(
        "--no-mask",
        dest="mask",
        action="store_false",
        help="Disable land-sea mask display",
    )
    parser.add_argument(
        "--max-depth",
        type=float,
        default=-2500.0,
        help="Maximum depth limit for color scale (default: -2500.0)",
    )
    parser.add_argument(
        "--max-orography",
        type=float,
        default=10.0,
        help="Maximum orography limit for land color scale in meters (default: 10.0)",
    )
    parser.add_argument(
        "--display",
        dest="display",
        action="store_true",
        default=True,
        help="Interactively display the figure window (default: enabled)",
    )
    parser.add_argument(
        "--no-display",
        dest="display",
        action="store_false",
        help="Disable interactive figure window display",
    )
    parser.add_argument(
        "--show",
        dest="display",
        action="store_true",
        help="Interactively display the figure window",
    )

    args = parser.parse_args()

    if not args.display:
        matplotlib.use("Agg")

    fmt = args.format.lower()
    if fmt == "jpeg":
        fmt = "jpg"

    if args.output is None:
        grid_name = extract_grid_name(args.input)
        out_path = f"{grid_name}.{fmt}"
    else:
        out_path = args.output

    data = load_grid_data(args.input)
    plot_grid(
        data,
        title=args.title,
        output_path=out_path,
        show=args.display,
        show_mask=args.mask,
        max_depth=args.max_depth,
        max_orography=args.max_orography,
    )


if __name__ == "__main__":
    main()
