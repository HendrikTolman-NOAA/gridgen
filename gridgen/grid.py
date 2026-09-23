# WAVEWATCH III (WW3) / WAVEWATCH IV (WW4) Gridgen Package
#
# Copyright 2026 National Weather Service (NWS), NOAA. All rights reserved.
# NWS often uses Generative AI (GenAI) for code development and refactoring.
# Whenever GenAI is used, NWS requires a full human review of code before it
# is added to its repositories.
#
# @author Aldgisl (Agentic AI), Hendrik Tolman
# @date Initial: 2026-09-22
#
# Code Heritage:
# Converted from generate_grid.m originally authored by NOAA/NCEP
# (Arun Chawla, Stylianos Flampouris, Deanna Spindler).

"""Bathymetry extraction and grid generation routines for WAVEWATCH III (WW3) / WAVEWATCH IV (WW4)."""

from __future__ import annotations

import os

import numpy as np
import xarray as xr
from shapely.geometry import Point, Polygon

from .geometry import compute_cellcorner


def generate_grid(
    x: np.ndarray,
    y: np.ndarray,
    ref_dir: str = "",
    bathy_source: str | xr.Dataset = "etopo1",
    limit: float = 0.5,
    cut_off: float = 0.1,
    dry: float = 999999.0,
    var_names: tuple[str, str, str] | None = None,
) -> np.ndarray:
    """Generate 2D bathymetry dataset from high resolution base bathymetry.

    Parameters
    ----------
    x : np.ndarray
        2D longitude grid array of shape (Ny, Nx).
    y : np.ndarray
        2D latitude grid array of shape (Ny, Nx).
    ref_dir : str
        Directory path containing reference NetCDF datasets.
    bathy_source : str | xr.Dataset
        Name of bathymetry source ('etopo1', 'etopo2') or pre-loaded xarray Dataset.
    limit : float
        Fraction (0..1) of wet base cells required to mark target cell wet.
    cut_off : float
        Cut-off depth to distinguish dry/wet cells (depths <= cut_off are wet).
    dry : float
        Depth value assigned to dry cells.
    var_names : Optional[Tuple[str, str, str]]
        Optional tuple of variable names for (lon, lat, depth) in NetCDF.

    Returns
    -------
    depth_sub : np.ndarray
        2D depth array of shape (Ny, Nx).
    """
    Ny, Nx = x.shape
    depth_sub = np.full((Ny, Nx), dry, dtype=np.float64)

    # 1. Load source bathymetry dataset
    if isinstance(bathy_source, xr.Dataset):
        ds_base = bathy_source
        if var_names is None:
            var_x = "lon" if "lon" in ds_base else "x"
            var_y = "lat" if "lat" in ds_base else "y"
            var_z = "z" if "z" in ds_base else "elevation"
        else:
            var_x, var_y, var_z = var_names
    else:
        if var_names is None:
            if bathy_source == "etopo2":
                fname_base = os.path.join(ref_dir, "etopo2.nc")
                var_x, var_y, var_z = "x", "y", "z"
            elif bathy_source == "etopo1":
                fname_base = os.path.join(ref_dir, "etopo1.nc")
                var_x, var_y, var_z = "lon", "lat", "z"
            else:
                fname_base = os.path.join(ref_dir, f"{bathy_source}.nc")
                var_x, var_y, var_z = "lon", "lat", "z"
        else:
            fname_base = os.path.join(ref_dir, f"{bathy_source}.nc")
            var_x, var_y, var_z = var_names

        if not os.path.exists(fname_base):
            # If bathymetry file does not exist, return default array or synthetic
            return depth_sub

        ds_base = xr.open_dataset(fname_base)

    lon_base = np.asarray(ds_base[var_x].values, dtype=np.float64)
    lat_base = np.asarray(ds_base[var_y].values, dtype=np.float64)
    z_base = np.asarray(ds_base[var_z].values, dtype=np.float64)

    if lon_base.ndim > 1 or lat_base.ndim > 1:
        # Flatten if 2D
        lon_base = lon_base.ravel()
        lat_base = lat_base.ravel()

    dx_base = float(np.abs(np.diff(lon_base).mean())) if len(lon_base) > 1 else 1.0
    dy_base = float(np.abs(np.diff(lat_base).mean())) if len(lat_base) > 1 else 1.0

    # 2. Iterate cells and interpolate/average
    for j in range(Nx):
        for k in range(Ny):
            c1, c2, c3, c4, wdth, hgt = compute_cellcorner(x, y, j, k)
            cell_poly = np.array([c4, c1, c2, c3, c4], dtype=np.float64)

            ndx = round(wdth / dx_base) if dx_base > 0 else 0
            ndy = round(hgt / dy_base) if dy_base > 0 else 0

            target_x = float(x[k, j])
            target_y = float(y[k, j])

            if ndx <= 1 and ndy <= 1:
                # Bilinear interpolation
                lon_idx = np.searchsorted(lon_base, target_x) - 1
                lat_idx = np.searchsorted(lat_base, target_y) - 1

                lon_idx = np.clip(lon_idx, 0, len(lon_base) - 2)
                lat_idx = np.clip(lat_idx, 0, len(lat_base) - 2)

                x1, x2 = lon_base[lon_idx], lon_base[lon_idx + 1]
                y1, y2 = lat_base[lat_idx], lat_base[lat_idx + 1]

                den = (x2 - x1) * (y2 - y1)
                if den == 0:
                    depth_val = float(z_base[lat_idx, lon_idx])
                else:
                    dx1 = target_x - x1
                    dx2 = x2 - target_x
                    dy1 = target_y - y1
                    dy2 = y2 - target_y

                    a11 = z_base[lat_idx, lon_idx]
                    a12 = z_base[lat_idx, lon_idx + 1]
                    a21 = z_base[lat_idx + 1, lon_idx]
                    a22 = z_base[lat_idx + 1, lon_idx + 1]

                    depth_val = (
                        a11 * dy2 * dx2
                        + a12 * dy2 * dx1
                        + a21 * dy1 * dx2
                        + a22 * dy1 * dx1
                    ) / den

                depth_sub[k, j] = depth_val if depth_val <= cut_off else dry
            else:
                # Cell averaging
                px = cell_poly[:, 0]
                py = cell_poly[:, 1]
                min_x, max_x = px.min(), px.max()
                min_y, max_y = py.min(), py.max()

                i_start = max(0, np.searchsorted(lon_base, min_x) - 1)
                i_end = min(len(lon_base), np.searchsorted(lon_base, max_x) + 1)
                j_start = max(0, np.searchsorted(lat_base, min_y) - 1)
                j_end = min(len(lat_base), np.searchsorted(lat_base, max_y) + 1)

                sub_z = z_base[j_start:j_end, i_start:i_end]
                if sub_z.size == 0:
                    depth_sub[k, j] = dry
                    continue

                poly_shape = Polygon(cell_poly)
                wet_depths = []
                total_pts = 0

                sub_lons = lon_base[i_start:i_end]
                sub_lats = lat_base[j_start:j_end]

                for jj, bx in enumerate(sub_lons):
                    for kk, by in enumerate(sub_lats):
                        if poly_shape.contains(Point(bx, by)):
                            total_pts += 1
                            zv = float(sub_z[kk, jj])
                            if zv <= cut_off:
                                wet_depths.append(zv)

                if total_pts > 0 and (len(wet_depths) / total_pts) >= limit:
                    depth_sub[k, j] = float(np.mean(wet_depths))
                else:
                    depth_sub[k, j] = dry

    if not isinstance(bathy_source, xr.Dataset) and 'ds_base' in locals():
        ds_base.close()

    return depth_sub
