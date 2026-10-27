# WAVEWATCH III (WW3) / WAVEWATCH IV (WW4) Gridgen Package
#
# Copyright 2026 National Weather Service (NWS), NOAA. All rights reserved.
# NWS often uses Generative AI (GenAI) for code development and refactoring.
# Whenever GenAI is used, NWS requires a full human review of code before it
# is added to its repositories.
#
# @file grid.py
# @brief Bathymetry extraction and grid generation routines for WW3 / WW4.
# @author Aldgisl (Agentic AI), Hendrik Tolman
# @author Jules (Agentic AI) (contributor)
# @date Initial: 2026-09-22
# @date Latest Update: 2026-10-27
#
# Code Heritage:
# Converted from generate_grid.m originally authored by NOAA/NCEP
# (Arun Chawla, Stylianos Flampouris, Deanna Spindler).

"""Bathymetry extraction and grid generation routines for WAVEWATCH III (WW3) / WAVEWATCH IV (WW4)."""

from __future__ import annotations

import os
import sys

import numpy as np
import shapely
import xarray as xr
from shapely.geometry import Polygon

from .coordinates import (
    create_grid_coordinates,
    create_regular_grid,
    create_rotated_pole_grid,
    create_stereographic_grid,
    validate_grid_parameters,
)
from .geometry import compute_all_corners

__all__ = [
    "create_grid_coordinates",
    "create_regular_grid",
    "create_rotated_pole_grid",
    "create_stereographic_grid",
    "generate_grid",
    "validate_grid_parameters",
]


def generate_grid(
    x: np.ndarray,
    y: np.ndarray,
    ref_dir: str = "",
    bathy_source: str | xr.Dataset = "etopo2",
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

    def _detect_var_names(ds: xr.Dataset) -> tuple[str, str, str]:
        var_x = None
        for cand in ["lon", "longitude", "x", "X", "lon_b", "lon_base"]:
            if cand in ds or cand in ds.coords or cand in ds.dims:
                var_x = cand
                break

        var_y = None
        for cand in ["lat", "latitude", "y", "Y", "lat_b", "lat_base"]:
            if cand in ds or cand in ds.coords or cand in ds.dims:
                var_y = cand
                break

        var_z = None
        for cand in ["elevation", "z", "height", "altitude", "bed_elevation", "z_base"]:
            if cand in ds.data_vars or cand in ds:
                var_z = cand
                break

        if var_z is None and len(ds.data_vars) == 1:
            var_z = next(iter(ds.data_vars.keys()))

        if var_x is None or var_y is None or var_z is None:
            raise KeyError(
                f"Could not automatically detect longitude/latitude/elevation variables in dataset. "
                f"Variables found: {list(ds.keys())}. Coords found: {list(ds.coords.keys())}."
            )
        return var_x, var_y, var_z

    # 1. Load source bathymetry dataset
    if isinstance(bathy_source, xr.Dataset):
        ds_base = bathy_source
        if var_names is None:
            var_x, var_y, var_z = _detect_var_names(ds_base)
        else:
            var_x, var_y, var_z = var_names
    else:
        if os.path.isabs(bathy_source) or os.path.exists(bathy_source):
            fname_base = bathy_source
        else:
            # Check for candidate filenames in ref_dir
            candidates = [f"{bathy_source}.nc"]
            if bathy_source in ("gebco", "gebco_2024", "GEBCO"):
                candidates.extend(["gebco_2024.nc", "gebco.nc", "GEBCO_2024.nc", "GEBCO_2024_CF.nc"])
            elif bathy_source == "etopo2":
                candidates.insert(0, "etopo2.nc")
            elif bathy_source in ("etopo1", "etopo_2022"):
                candidates.extend(["etopo1.nc", "etopo_2022.nc", "ETOPO_2022_v1_60s_N90W180_bed.nc"])

            fname_base = None
            for cand in candidates:
                cand_path = os.path.join(ref_dir, cand)
                if os.path.exists(cand_path):
                    fname_base = cand_path
                    break

            if fname_base is None:
                fname_base = os.path.join(ref_dir, f"{bathy_source}.nc")

        if not os.path.exists(fname_base):
            raise FileNotFoundError(
                f"Reference bathymetry dataset file '{fname_base}' was not found. "
                f"Please populate reference data using populate_reference_data.sh."
            )

        ds_base = xr.open_dataset(fname_base)

        if var_names is None:
            if bathy_source == "etopo2" and "x" in ds_base and "y" in ds_base and "z" in ds_base:
                var_x, var_y, var_z = "x", "y", "z"
            elif bathy_source == "etopo1" and "lon" in ds_base and "lat" in ds_base and "z" in ds_base:
                var_x, var_y, var_z = "lon", "lat", "z"
            else:
                var_x, var_y, var_z = _detect_var_names(ds_base)
        else:
            var_x, var_y, var_z = var_names

    lon_base = np.asarray(ds_base[var_x].values, dtype=np.float64)
    lat_base = np.asarray(ds_base[var_y].values, dtype=np.float64)
    z_base = np.asarray(ds_base[var_z].values, dtype=np.float64)

    if len(lon_base) > 1 and lon_base[1] < lon_base[0]:
        lon_order = np.argsort(lon_base)
        lon_base = lon_base[lon_order]
        z_base = z_base[:, lon_order] if z_base.ndim == 2 else z_base[lon_order]

    if len(lat_base) > 1 and lat_base[1] < lat_base[0]:
        lat_order = np.argsort(lat_base)
        lat_base = lat_base[lat_order]
        z_base = z_base[lat_order, :] if z_base.ndim == 2 else z_base[lat_order]

    if lon_base.ndim > 1 or lat_base.ndim > 1:
        # Flatten if 2D
        lon_base = lon_base.ravel()
        lat_base = lat_base.ravel()

    dx_base = float(np.abs(np.diff(lon_base).mean())) if len(lon_base) > 1 else 1.0
    dy_base = float(np.abs(np.diff(lat_base).mean())) if len(lat_base) > 1 else 1.0

    lon_min_b = float(lon_base.min()) if len(lon_base) > 0 else 0.0
    lon_max_b = float(lon_base.max()) if len(lon_base) > 0 else 360.0
    lon_span_b = lon_max_b - lon_min_b

    # 2. Iterate cells and interpolate/average
    polygons_cell, widths, heights = compute_all_corners(x, y)

    ndx_all = np.round(widths / dx_base) if dx_base > 0 else np.zeros((Ny, Nx))
    ndy_all = np.round(heights / dy_base) if dy_base > 0 else np.zeros((Ny, Nx))

    fine_mask = (ndx_all <= 1) & (ndy_all <= 1)

    target_x = x.copy()
    target_y = y.copy()

    if lon_span_b >= 350.0:
        if lon_min_b >= -1.0 and lon_max_b <= 360.1:
            target_x = (target_x - lon_min_b) % 360.0 + lon_min_b
        elif lon_min_b >= -180.1 and lon_max_b <= 180.1:
            target_x = (target_x + 180.0) % 360.0 - 180.0

    # Bilinear interpolation for fine cells
    if np.any(fine_mask):
        fine_tx = target_x[fine_mask]
        fine_ty = target_y[fine_mask]

        lon_idx = np.searchsorted(lon_base, fine_tx) - 1
        lat_idx = np.searchsorted(lat_base, fine_ty) - 1

        lon_idx = np.clip(lon_idx, 0, len(lon_base) - 2)
        lat_idx = np.clip(lat_idx, 0, len(lat_base) - 2)

        x1, x2 = lon_base[lon_idx], lon_base[lon_idx + 1]
        y1, y2 = lat_base[lat_idx], lat_base[lat_idx + 1]

        den = (x2 - x1) * (y2 - y1)
        zero_den = (den == 0)

        dx1 = fine_tx - x1
        dx2 = x2 - fine_tx
        dy1 = fine_ty - y1
        dy2 = y2 - fine_ty

        a11 = z_base[lat_idx, lon_idx]
        a12 = z_base[lat_idx, lon_idx + 1]
        a21 = z_base[lat_idx + 1, lon_idx]
        a22 = z_base[lat_idx + 1, lon_idx + 1]

        depth_vals = (
            a11 * dy2 * dx2
            + a12 * dy2 * dx1
            + a21 * dy1 * dx2
            + a22 * dy1 * dx1
        ) / np.where(zero_den, 1.0, den)
        depth_vals[zero_den] = a11[zero_den]

        depth_sub[fine_mask] = depth_vals

    # Cell averaging for coarse cells
    coarse_k, coarse_j = np.where(~fine_mask)
    num_coarse = len(coarse_k)

    if num_coarse > 0:
        last_pct = -1.0
        for idx, (k, j) in enumerate(zip(coarse_k, coarse_j)):
            pct = ((idx + 1) / num_coarse) * 100.0
            curr_pct = round(pct, 1)
            if curr_pct != last_pct or idx == num_coarse - 1:
                last_pct = curr_pct
                sys.stdout.write(f"\r  Extracting bathymetry depths... {pct:5.1f}%")
                sys.stdout.flush()

            cell_poly = polygons_cell[k, j]
            cell_poly_q = cell_poly.copy()
            cell_tx = target_x[k, j]

            if lon_span_b >= 350.0:
                rel_lons = cell_poly_q[:, 0] - cell_tx
                rel_lons = (rel_lons + 180.0) % 360.0 - 180.0
                cell_poly_q[:, 0] = cell_tx + rel_lons

            px = cell_poly_q[:, 0]
            py = cell_poly_q[:, 1]
            min_x, max_x = px.min(), px.max()
            min_y, max_y = py.min(), py.max()
            if min_x > max_x:
                min_x, max_x = max_x, min_x
            if min_y > max_y:
                min_y, max_y = max_y, min_y

            j_start = max(0, np.searchsorted(lat_base, min_y) - 1)
            j_end = min(len(lat_base), np.searchsorted(lat_base, max_y) + 1)
            sub_lats = lat_base[j_start:j_end]

            if lon_span_b >= 350.0 and (min_x < lon_min_b or max_x > lon_max_b):
                sub_lons_list = []
                sub_z_list = []

                x_ranges = []
                if min_x < lon_min_b:
                    x_ranges.append((min_x + 360.0, lon_max_b, -360.0))
                    x_ranges.append((lon_min_b, max_x, 0.0))
                elif max_x > lon_max_b:
                    x_ranges.append((min_x, lon_max_b, 0.0))
                    x_ranges.append((lon_min_b, max_x - 360.0, 360.0))
                else:
                    x_ranges.append((min_x, max_x, 0.0))

                for r_min, r_max, offset in x_ranges:
                    if r_min <= r_max:
                        i_s = max(0, np.searchsorted(lon_base, r_min) - 1)
                        i_e = min(len(lon_base), np.searchsorted(lon_base, r_max) + 1)
                        if i_e > i_s:
                            sub_lons_list.append(lon_base[i_s:i_e] + offset)
                            sub_z_list.append(z_base[j_start:j_end, i_s:i_e])

                if sub_lons_list and sub_z_list:
                    sub_lons = np.concatenate(sub_lons_list)
                    sub_z = np.hstack(sub_z_list)
                else:
                    sub_lons = np.array([], dtype=np.float64)
                    sub_z = np.empty((len(sub_lats), 0), dtype=np.float64)
            else:
                i_start = max(0, np.searchsorted(lon_base, min_x) - 1)
                i_end = min(len(lon_base), np.searchsorted(lon_base, max_x) + 1)
                sub_lons = lon_base[i_start:i_end]
                sub_z = z_base[j_start:j_end, i_start:i_end]

            if sub_z.size == 0 or len(sub_lats) == 0 or len(sub_lons) == 0:
                depth_sub[k, j] = dry
                continue

            poly_shape = Polygon(cell_poly_q)
            grid_x, grid_y = np.meshgrid(sub_lons, sub_lats)
            inside = shapely.contains_xy(poly_shape, grid_x, grid_y)

            total_pts = int(np.sum(inside))
            if total_pts > 0:
                pts_z = sub_z[inside]
                wet_mask = pts_z <= cut_off
                wet_pts = pts_z[wet_mask]
                if (len(wet_pts) / total_pts) >= limit:
                    depth_sub[k, j] = float(np.mean(wet_pts))
                else:
                    depth_sub[k, j] = dry
            else:
                depth_sub[k, j] = dry

    total_cells = Nx * Ny
    if total_cells > 0:
        sys.stdout.write("\r  Extracting bathymetry depths... 100.0%\n")
        sys.stdout.flush()

    if not isinstance(bathy_source, xr.Dataset) and "ds_base" in locals():
        ds_base.close()

    return depth_sub
