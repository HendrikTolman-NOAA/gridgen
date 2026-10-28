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
# @date Latest Update: 2026-10-28
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
import matplotlib.ticker as mticker
import numpy as np
import xarray as xr
from mpl_toolkits.axes_grid1.inset_locator import inset_axes

from .io.ascii import read_ww3file, read_ww3meta, read_ww3obstr


def fmt_lon(x: float, pos: Any = None) -> str:
    """Format longitude ticks into traditional [-180, 180] East/West degrees."""
    lon_deg = (x + 180.0) % 360.0 - 180.0
    lon_deg = round(lon_deg, 4)
    if abs(lon_deg) < 1e-4 or abs(abs(lon_deg) - 180.0) < 1e-4:
        return f"{round(abs(lon_deg))}°"
    elif lon_deg < 0:
        return f"{abs(lon_deg):g}°W"
    else:
        return f"{lon_deg:g}°E"


def fmt_lat(y: float, pos: Any = None) -> str:
    """Format latitude ticks into North/South degrees."""
    lat_deg = round(y, 4)
    if abs(lat_deg) < 1e-4:
        return "0°"
    elif lat_deg < 0:
        return f"{abs(lat_deg):g}°S"
    else:
        return f"{lat_deg:g}°N"


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
        Dictionary containing 'lon', 'lat', 'depth', 'mask', 'ObsX', and 'ObsY' 2D numpy arrays.
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
            ObsX = ds["grid_ObsX"].values if "grid_ObsX" in ds else (ds["ObsX"].values if "ObsX" in ds else (ds["grid_sx"].values if "grid_sx" in ds else (ds["sx"].values if "sx" in ds else None)))
            ObsY = ds["grid_ObsY"].values if "grid_ObsY" in ds else (ds["ObsY"].values if "ObsY" in ds else (ds["grid_sy"].values if "grid_sy" in ds else (ds["sy"].values if "sy" in ds else None)))

        # UGRID 1.0 format fallback
        elif "face_lon" in ds and "face_lat" in ds:
            face_lon = ds["face_lon"].values
            face_lat = ds["face_lat"].values
            depth_raw = ds["depth"].values if "depth" in ds else np.zeros_like(face_lon)
            mask_raw = ds["mask"].values if "mask" in ds else np.ones_like(face_lon)
            ObsX_raw = ds["ObsX"].values if "ObsX" in ds else (ds["sx"].values if "sx" in ds else None)
            ObsY_raw = ds["ObsY"].values if "ObsY" in ds else (ds["sy"].values if "sy" in ds else None)

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
                ObsX = ObsX_raw.reshape(Ny, Nx) if ObsX_raw is not None else None
                ObsY = ObsY_raw.reshape(Ny, Nx) if ObsY_raw is not None else None
            else:
                lon = face_lon
                lat = face_lat
                depth = depth_raw
                mask = mask_raw
                ObsX = ObsX_raw
                ObsY = ObsY_raw

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
            ObsX = ds["ObsX"].values if "ObsX" in ds else (ds["sx"].values if "sx" in ds else None)
            ObsY = ds["ObsY"].values if "ObsY" in ds else (ds["sy"].values if "sy" in ds else None)

        bathy_src = str(ds.attrs.get("bathy_source", ds.attrs.get("source", "etopo2")))
        bound_src = str(ds.attrs.get("bound_source", ds.attrs.get("bound_file", ds.attrs.get("coast_file", ""))))
        ds.close()
        return {
            "lon": lon,
            "lat": lat,
            "depth": depth,
            "mask": mask,
            "ObsX": ObsX,
            "ObsY": ObsY,
            "filename": path.name,
            "bathy_source": bathy_src,
            "bound_source": bound_src,
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
            ObsX_raw, ObsY_raw = read_ww3obstr(obstr_file, Ny, Nx)
            ObsX = ObsX_raw * obstr_scale
            ObsY = ObsY_raw * obstr_scale
        else:
            ObsX, ObsY = None, None

        return {
            "lon": lon,
            "lat": lat,
            "depth": depth,
            "mask": mask,
            "ObsX": ObsX,
            "ObsY": ObsY,
            "filename": path.name,
            "bathy_source": "etopo2",
            "bound_source": "coastal_bound_low.mat",
        }

    raise FileNotFoundError(
        f"Could not load grid data from path or prefix '{filepath}'"
    )


def _parse_coord_token(s: str) -> float:
    """Parse floating-point coordinate token supporting degrees, cardinal directions, and trailing/leading dots."""
    token = str(s).strip()
    if not token:
        raise ValueError("Empty coordinate token")
    mult = 1.0
    upper_tok = token.upper()
    if upper_tok.endswith(("W", "S")):
        mult = -1.0
        token = token[:-1]
    elif upper_tok.endswith(("N", "E")):
        token = token[:-1]
    token = token.replace("°", "").strip()
    return float(token) * mult


def format_coastline_desc(bound_source: str | None) -> str | None:
    """Format boundary polygon filename or identifier into coastline description string.

    Parameters
    ----------
    bound_source : str or None
        Path, filename, or name of boundary polygon file (e.g. 'coastal_bound_low.mat').

    Returns
    -------
    str or None
        Human-readable coastline description string (e.g. 'low res coastline') or None if disabled/unspecified.
    """
    if not bound_source or str(bound_source).lower() in ("none", ""):
        return None
    name = Path(bound_source).name.lower()
    if "coarse" in name:
        return "coarse res coastline"
    elif "low" in name:
        return "low res coastline"
    elif "inter" in name:
        return "intermediate res coastline"
    elif "high" in name:
        return "high res coastline"
    elif "full" in name:
        return "full res coastline"
    else:
        clean = Path(bound_source).stem
        return f"{clean} coastline"


def parse_zoom_args(zoom_input: Any) -> tuple[float, float, float] | None:
    """Parse zoom parameter from tuple/list, string, or CLI sequence.

    Parameters
    ----------
    zoom_input : Any
        Zoom input specification (e.g., (-70, 40, 2), ["-70", "40", "2"], or "-70 40 2").

    Returns
    -------
    tuple[float, float, float] or None
        Parsed (central_lon, central_lat, zoom_factor) tuple, or None if zoom_input is None.
    """
    if zoom_input is None:
        return None
    parts = []
    if isinstance(zoom_input, (list, tuple)):
        if len(zoom_input) == 0:
            return None
        for item in zoom_input:
            if isinstance(item, str):
                clean_item = item.replace(",", " ")
                for token in clean_item.split():
                    parts.append(_parse_coord_token(token))
            else:
                parts.append(float(item))
    elif isinstance(zoom_input, str):
        clean_item = zoom_input.replace(",", " ")
        for token in clean_item.split():
            parts.append(_parse_coord_token(token))
    else:
        raise TypeError("zoom parameter must be a tuple, list, or string of 3 numbers")

    if len(parts) != 3:
        raise ValueError(
            f"Zoom expects 3 values (central_lon, central_lat, zoom_factor), got {len(parts)} values from '{zoom_input}'"
        )
    return (parts[0], parts[1], parts[2])


def plot_grid(
    data: dict[str, Any],
    title: str | None = None,
    subtitle: str | None = "Bathymetry, Orography, and Obstructions",
    output_path: str | Path | None = None,
    show: bool = False,
    show_mask: bool = True,
    max_depth: float | None = -8000.0,
    max_orography: float | None = 10.0,
    zoom: tuple[float, float, float] | list[float] | str | None = None,
    bathy_source: str | None = None,
    bound_source: str | None = None,
) -> matplotlib.figure.Figure:
    """Graphically display resulting grid bathymetry, orography, and obstructions plot.

    Parameters
    ----------
    data : dict[str, Any]
        Dictionary containing grid data ('lon', 'lat', 'depth', 'mask', 'ObsX', 'ObsY').
    title : str, optional
        Main figure title string (default: input dataset filename). Can be set to empty string to disable.
    subtitle : str, optional
        Figure subtitle string (default: "Bathymetry, Orography, and Obstructions"). Can be set to empty string to disable.
    output_path : str or Path, optional
        File path where the resulting plot figure should be saved.
    show : bool
        If True, call matplotlib plt.show() to display interactively.
    show_mask : bool
        If True, mask out dry land cells (mask == 0) and use dark green background. Default is True.
    max_depth : float, optional
        Maximum depth (minimum numerical bathymetry limit, e.g., -8000.0) for color scale range limit. Default is -8000.0.
    max_orography : float, optional
        Maximum orography elevation limit in meters (default: 10.0) for land color scale.
    zoom : tuple or list of (central_lon, central_lat, zoom_factor), optional
        Zoom view centered at (central_lon, central_lat) with zoom_factor. A zoom_factor of 1 shifts the view frame.

    Returns
    -------
    matplotlib.figure.Figure
        Created Matplotlib figure object.
    """
    lon = data["lon"]
    lat = data["lat"]
    depth = data["depth"].copy()
    mask = data["mask"]
    ObsX = data.get("ObsX", data.get("sx", None))
    ObsY = data.get("ObsY", data.get("sy", None))

    # Compute combined maximum obstruction map: Obs = max(ObsX, ObsY)
    Obs_max = None
    if ObsX is not None and ObsY is not None:
        Obs_max = np.maximum(ObsX, ObsY)

    has_obstr = (
        Obs_max is not None
        and bool(np.any(Obs_max >= 0.01))
    )

    fig, ax1 = plt.subplots(figsize=(8, 5))

    dark_green = "#1b4332"  # Dark green background for land/sea mask
    if show_mask:
        ax1.set_facecolor(dark_green)

    depth_limit = -abs(max_depth) if max_depth is not None else -8000.0
    vmax_orog = max_orography if max_orography is not None else 10.0

    zoom_parsed = parse_zoom_args(zoom)

    # Separate underwater bathymetry (depth <= 0) and land orography (depth > 0)
    bathymetry_mask = (depth <= 0) & (mask != 0) if show_mask else (depth <= 0)
    orography_mask = (depth > 0) & (depth < 999999.0) & (mask != 0) if show_mask else ((depth > 0) & (depth < 999999.0))
    boundary_mask = (mask == 2)
    has_boundary = bool(np.any(boundary_mask))

    depth_bathy = np.where(bathymetry_mask, depth, np.nan)
    depth_orog = np.where(orography_mask, np.clip(depth, 0.0, vmax_orog), np.nan)

    vmin_bathy = depth_limit
    vmax_bathy = 0.0

    lon_min, lon_max = float(np.nanmin(lon)), float(np.nanmax(lon))
    lat_min, lat_max = float(np.nanmin(lat)), float(np.nanmax(lat))

    span_lon_raw = lon_max - lon_min if lon_max > lon_min else 1.0
    span_lat_raw = lat_max - lat_min if lat_max > lat_min else 1.0

    is_global = bool(span_lon_raw >= 350.0)

    if is_global:
        if lon.ndim == 2:
            lon_plot = np.hstack([lon - 720.0, lon - 360.0, lon, lon + 360.0, lon + 720.0])
            lat_plot = np.hstack([lat, lat, lat, lat, lat])
            depth_bathy_plot = np.hstack([depth_bathy, depth_bathy, depth_bathy, depth_bathy, depth_bathy])
            depth_orog_plot = np.hstack([depth_orog, depth_orog, depth_orog, depth_orog, depth_orog])
            boundary_plot = np.hstack([boundary_mask, boundary_mask, boundary_mask, boundary_mask, boundary_mask])
        else:
            lon_plot = np.concatenate([lon - 720.0, lon - 360.0, lon, lon + 360.0, lon + 720.0])
            lat_plot = np.concatenate([lat, lat, lat, lat, lat])
            depth_bathy_plot = np.concatenate([depth_bathy, depth_bathy, depth_bathy, depth_bathy, depth_bathy])
            depth_orog_plot = np.concatenate([depth_orog, depth_orog, depth_orog, depth_orog, depth_orog])
            boundary_plot = np.concatenate([boundary_mask, boundary_mask, boundary_mask, boundary_mask, boundary_mask])
    else:
        lon_plot = lon
        lat_plot = lat
        depth_bathy_plot = depth_bathy
        depth_orog_plot = depth_orog
        boundary_plot = boundary_mask

    if lon_plot.ndim == 2:
        pcm1 = ax1.pcolormesh(
            lon_plot, lat_plot, depth_bathy_plot, cmap="Blues_r", vmin=vmin_bathy, vmax=vmax_bathy, shading="nearest"
        )
        pcm2 = ax1.pcolormesh(
            lon_plot, lat_plot, depth_orog_plot, cmap="YlGn", vmin=0.0, vmax=vmax_orog, shading="nearest"
        )
    else:
        pcm1 = ax1.scatter(lon_plot, lat_plot, c=depth_bathy_plot, cmap="Blues_r", vmin=vmin_bathy, vmax=vmax_bathy)
        pcm2 = ax1.scatter(lon_plot, lat_plot, c=depth_orog_plot, cmap="YlGn", vmin=0.0, vmax=vmax_orog)

    if has_boundary:
        bnd_display = np.where(boundary_plot, 1.0, np.nan)
        magenta = "#ff00ff"  # Vibrant magenta color for input boundary cells (mask value 2)
        cmap_bnd = matplotlib.colors.ListedColormap([magenta])
        if lon_plot.ndim == 2:
            ax1.pcolormesh(
                lon_plot, lat_plot, bnd_display, cmap=cmap_bnd, vmin=0.5, vmax=1.5, shading="nearest"
            )
        else:
            ax1.scatter(
                lon_plot, lat_plot, c=bnd_display, cmap=cmap_bnd, vmin=0.5, vmax=1.5
            )

    pcm_Obs = None
    if has_obstr:
        if is_global:
            if Obs_max.ndim == 2:
                Obs_plot = np.hstack([Obs_max, Obs_max, Obs_max, Obs_max, Obs_max])
            else:
                Obs_plot = np.concatenate([Obs_max, Obs_max, Obs_max, Obs_max, Obs_max])
        else:
            Obs_plot = Obs_max

        # Mask out values < 0.01 so nothing is plotted for obstructions < 0.01
        Obs_plot = np.where(Obs_plot >= 0.01, Obs_plot, np.nan)

        if lon_plot.ndim == 2:
            pcm_Obs = ax1.pcolormesh(
                lon_plot, lat_plot, Obs_plot, cmap="YlOrRd", vmin=0.0, vmax=1.0, shading="nearest"
            )
        else:
            pcm_Obs = ax1.scatter(lon_plot, lat_plot, c=Obs_plot, cmap="YlOrRd", vmin=0.0, vmax=1.0)

    ax1.xaxis.set_major_formatter(mticker.FuncFormatter(fmt_lon))
    ax1.yaxis.set_major_formatter(mticker.FuncFormatter(fmt_lat))

    if title is not None:
        main_title = title
    else:
        fname = data.get("filename", "ww4_grid_ugrid.nc")
        main_title = fname if fname.startswith("WAVEWATCH IV grid") else f"WAVEWATCH IV grid {fname}"

    sub_text = ""
    if subtitle:
        bsource = bathy_source or data.get("bathy_source") or "etopo2"
        raw_bound_src = bound_source if bound_source is not None else data.get("bound_source")
        if raw_bound_src is None or raw_bound_src == "":
            raw_bound_src = "coastal_bound_low.mat"
        c_desc = format_coastline_desc(raw_bound_src)

        details = [d for d in [bsource, c_desc] if d]
        if details:
            detail_str = ", ".join(details)
            if f"({detail_str})" not in subtitle:
                sub_text = f"{subtitle} ({detail_str})"
            else:
                sub_text = subtitle
        else:
            sub_text = subtitle

    if zoom_parsed is not None and zoom_parsed[2] > 1.0:
        xlabel_str = "Longitude (zoom)"
        ylabel_str = "Latitude (zoom)"
    else:
        xlabel_str = "Longitude"
        ylabel_str = "Latitude"

    ax1.set_xlabel(xlabel_str)
    ax1.set_ylabel(ylabel_str)

    ax1.grid(True, linestyle="--", alpha=0.5)

    if main_title and sub_text:
        ax1.set_title(sub_text, fontsize=10, fontweight="normal", pad=6)
        ax1.text(0.5, 1.08, main_title, transform=ax1.transAxes, ha="center", va="bottom", fontsize=14, fontweight="bold")
    elif main_title:
        ax1.set_title(main_title, fontsize=14, fontweight="bold", pad=10)
    elif sub_text:
        ax1.set_title(sub_text, fontsize=10, fontweight="normal", pad=10)

    if zoom_parsed is not None:
        central_lon, central_lat, zoom_factor = zoom_parsed
        zoom_factor = max(zoom_factor, 1.0)

        if is_global:
            # For global grids, lon_plot spans 5 tiles [lon_min - 720, lon_max + 720]
            # Keep user central_lon if inside valid plot range [-720, 720], otherwise normalize modulo 360
            if (lon_min - 720.0) <= central_lon <= (lon_max + 720.0):
                c_lon = central_lon
            else:
                c_lon = lon_min + (central_lon - lon_min) % 360.0
        else:
            # Normalize central longitude modulo 360 into base grid range [lon_min, lon_max]
            c_lon = lon_min + (central_lon - lon_min) % 360.0
            if np.isclose(c_lon, lon_min) and abs(central_lon - lon_max) < abs(central_lon - lon_min):
                c_lon = lon_max

        new_span_lat = span_lat_raw / zoom_factor
        if new_span_lat >= span_lat_raw:
            ylim = (lat_min, lat_max)
        else:
            ymin = central_lat - new_span_lat / 2.0
            ymax = central_lat + new_span_lat / 2.0
            if ymin < lat_min:
                ymin = lat_min
                ymax = lat_min + new_span_lat
            if ymax > lat_max:
                ymax = lat_max
                ymin = lat_max - new_span_lat
            ylim = (ymin, ymax)

        if is_global:
            new_span_lon = 360.0 / zoom_factor
            xlim = (c_lon - new_span_lon / 2.0, c_lon + new_span_lon / 2.0)
        else:
            new_span_lon = span_lon_raw / zoom_factor
            if new_span_lon >= span_lon_raw:
                xlim = (lon_min, lon_max)
            else:
                xmin = c_lon - new_span_lon / 2.0
                xmax = c_lon + new_span_lon / 2.0
                if xmin < lon_min:
                    xmin = lon_min
                    xmax = lon_min + new_span_lon
                if xmax > lon_max:
                    xmax = lon_max
                    xmin = lon_max - new_span_lon
                xlim = (xmin, xmax)

        ax1.set_xlim(xlim)
        ax1.set_ylim(ylim)
        aspect = 1.0 / max(np.cos(np.radians(central_lat)), 0.01)
        ax1.set_aspect(aspect)
        print(f"Applying zoom centered at ({c_lon:.4f}°, {central_lat:.4f}°) with zoom factor {zoom_factor:g}")
    elif is_global:
        ax1.set_xlim(lon_min, lon_max)
        ax1.set_ylim(lat_min, lat_max)

    fig.tight_layout()

    has_orography = bool(np.any(~np.isnan(depth_orog)))

    if has_orography:
        # 3 colorbars with nominal spacing (gap = 3%): Subgrid Obstruction Factor (top), Orography (middle), Bathymetry Depth (bottom)
        cax_obstr = inset_axes(
            ax1,
            width="3.5%",
            height="100%",
            loc="lower left",
            bbox_to_anchor=(1.03, 0.6867, 1, 0.3133),
            bbox_transform=ax1.transAxes,
            borderpad=0,
        )
        cax_orog = inset_axes(
            ax1,
            width="3.5%",
            height="100%",
            loc="lower left",
            bbox_to_anchor=(1.03, 0.3433, 1, 0.3133),
            bbox_transform=ax1.transAxes,
            borderpad=0,
        )
        cax_bathy = inset_axes(
            ax1,
            width="3.5%",
            height="100%",
            loc="lower left",
            bbox_to_anchor=(1.03, 0.0, 1, 0.3133),
            bbox_transform=ax1.transAxes,
            borderpad=0,
        )

        cb_orog = fig.colorbar(pcm2, cax=cax_orog, label="Orography (m)")
        cb_orog.ax.tick_params(labelsize=5)
        cb_orog.ax.yaxis.label.set_fontsize(6)
    else:
        # 2 colorbars with nominal spacing (gap = 3%): Subgrid Obstruction Factor (top), Bathymetry Depth (bottom)
        cax_obstr = inset_axes(
            ax1,
            width="3.5%",
            height="100%",
            loc="lower left",
            bbox_to_anchor=(1.03, 0.515, 1, 0.485),
            bbox_transform=ax1.transAxes,
            borderpad=0,
        )
        cax_bathy = inset_axes(
            ax1,
            width="3.5%",
            height="100%",
            loc="lower left",
            bbox_to_anchor=(1.03, 0.0, 1, 0.485),
            bbox_transform=ax1.transAxes,
            borderpad=0,
        )

    if has_obstr and pcm_Obs is not None:
        cb_obstr = fig.colorbar(pcm_Obs, cax=cax_obstr, label="Subgrid Obstruction Factor")
        cb_obstr.ax.tick_params(labelsize=5)
        cb_obstr.ax.yaxis.label.set_fontsize(6)
    else:
        cax_obstr.axis("off")
        cax_obstr.text(
            0.5,
            0.5,
            "Grid contains no obstructions",
            ha="center",
            va="center",
            rotation=90,
            fontsize=6,
            color="black",
        )

    cb_bathy = fig.colorbar(pcm1, cax=cax_bathy, label="Bathymetry Depth (m)")
    cb_bathy.ax.tick_params(labelsize=5)
    cb_bathy.ax.yaxis.label.set_fontsize(6)

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


def _is_option_flag(val: str) -> bool:
    """Check if token is a CLI option flag starting with hyphen and letter."""
    if not val.startswith("-"):
        return False
    clean = val.lstrip("-")
    if not clean:
        return False
    return bool(clean[0].isalpha() and not any(c.isdigit() for c in val))


def main() -> None:
    """CLI driver for displaying resulting grid bathymetry."""
    import sys

    # Preprocess sys.argv to combine zoom tokens into --zoom="LON LAT FACTOR" format
    new_argv = []
    idx = 0
    while idx < len(sys.argv):
        arg = sys.argv[idx]
        if arg == "--zoom" and idx + 1 < len(sys.argv):
            zoom_tokens = []
            j = idx + 1
            while j < len(sys.argv):
                val = sys.argv[j]
                # Stop if encountering another option flag like -i, -o, --no-display, etc.
                if _is_option_flag(val):
                    break
                zoom_tokens.append(val)
                j += 1
            if zoom_tokens:
                new_argv.append(f"--zoom={' '.join(zoom_tokens)}")
                idx = j
                continue
        new_argv.append(arg)
        idx += 1
    sys.argv = new_argv

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
        default=None,
        help="Figure main title (default: input dataset filename)",
    )
    parser.add_argument(
        "--no-title",
        dest="title",
        action="store_const",
        const="",
        help="Disable main figure title",
    )
    parser.add_argument(
        "--subtitle",
        type=str,
        default="Bathymetry, Orography, and Obstructions",
        help="Figure subtitle (default: Bathymetry, Orography, and Obstructions)",
    )
    parser.add_argument(
        "--no-subtitle",
        dest="subtitle",
        action="store_const",
        const="",
        help="Disable figure subtitle",
    )
    parser.add_argument(
        "--bathy-source",
        type=str,
        default=None,
        help="Bathymetry reference dataset identifier for subtitle (default: auto from dataset metadata)",
    )
    parser.add_argument(
        "--bound-source",
        "--bound-file",
        dest="bound_source",
        type=str,
        default=None,
        help="Shoreline boundary dataset file path or name for subtitle (default: auto from dataset metadata)",
    )
    parser.add_argument(
        "--no-mask",
        dest="mask",
        action="store_false",
        default=True,
        help="Disable land-sea mask display",
    )
    parser.add_argument(
        "--zoom",
        nargs="+",
        default=None,
        help="Zoom view centered at central longitude, central latitude with zoom factor (e.g. --zoom -70 40 2 or --zoom '-70,40,2')",
    )
    parser.add_argument(
        "--max-depth",
        type=float,
        default=-8000.0,
        help="Maximum depth limit for color scale (default: -8000.0)",
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
        subtitle=args.subtitle,
        output_path=out_path,
        show=args.display,
        show_mask=args.mask,
        max_depth=args.max_depth,
        max_orography=args.max_orography,
        zoom=args.zoom,
        bathy_source=args.bathy_source,
        bound_source=args.bound_source,
    )


if __name__ == "__main__":
    main()
