# WAVEWATCH III (WW3) / WAVEWATCH IV (WW4) Gridgen Package
#
# Copyright 2026 National Weather Service (NWS), NOAA. All rights reserved.
# NWS often uses Generative AI (GenAI) for code development and refactoring.
# Whenever GenAI is used, NWS requires a full human review of code before it
# is added to its repositories.
#
# @file obstructions.py
# @brief Subgrid obstruction calculation routines for WAVEWATCH III / WAVEWATCH IV.
# @author Aldgisl (Agentic AI), Hendrik Tolman
# @author Jules (Agentic AI) (contributor)
# @date Initial: 2026-09-22
# @date Latest Update: 2026-10-27
#
# Code Heritage:
# Converted from create_obstr.m originally authored by NOAA/NCEP
# (Arun Chawla).

"""Subgrid obstruction calculation routines for WAVEWATCH III (WW3) / WAVEWATCH IV (WW4)."""

from __future__ import annotations

import sys
from typing import Any

import numpy as np
import shapely
from shapely import STRtree
from shapely.geometry import Polygon

from .geometry import compute_all_corners


def create_obstr(
    x: np.ndarray,
    y: np.ndarray,
    bound_list: list[dict[str, Any]],
    mask: np.ndarray,
    offset_left: int = 1,
    offset_right: int = 1,
) -> tuple[np.ndarray, np.ndarray]:
    """Generate subgrid obstruction grids ObsX and ObsY.

    Parameters
    ----------
    x : np.ndarray
        2D array of longitudes of shape (Ny, Nx).
    y : np.ndarray
        2D array of latitudes of shape (Ny, Nx).
    bound_list : List[Dict[str, Any]]
        List of boundary polygon dictionaries.
    mask : np.ndarray
        2D land/sea mask array (1 = wet, 0 = dry).
    offset_left : int
        Search offset to the left/bottom neighbor.
    offset_right : int
        Search offset to the right/top neighbor.

    Returns
    -------
    ObsX, ObsY : np.ndarray
        2D obstruction arrays in x and y directions of shape (Ny, Nx).
        Values range from 0.0 (no obstruction) to 1.0 (full obstruction).
    """
    Ny, Nx = x.shape
    ObsX = np.zeros((Ny, Nx), dtype=np.float64)
    ObsY = np.zeros((Ny, Nx), dtype=np.float64)

    if not bound_list:
        return ObsX, ObsY

    grid_x_min = float(np.min(x))
    grid_x_max = float(np.max(x))
    dx = float(abs(x[0, 1] - x[0, 0])) if x.ndim == 2 and x.shape[1] > 1 else 1.0
    gx_min = grid_x_min - dx
    gx_max = grid_x_max + dx

    polygons = []
    for b in bound_list:
        bx = np.squeeze(np.asarray(b["x"], dtype=np.float64))
        by = np.squeeze(np.asarray(b["y"], dtype=np.float64))
        if len(bx) < 3:
            continue

        p_west, p_east = float(np.min(bx)), float(np.max(bx))

        k_min = int(np.floor((gx_min - p_east) / 360.0))
        k_max = int(np.ceil((gx_max - p_west) / 360.0))

        for k in range(k_min, k_max + 1):
            shift_x = k * 360.0
            s_west = p_west + shift_x
            s_east = p_east + shift_x

            if s_east < gx_min or s_west > gx_max:
                continue

            bx_shifted = bx + shift_x
            poly_coords = np.column_stack((bx_shifted, by))
            p = Polygon(poly_coords)
            if not p.is_valid:
                p = p.buffer(0)
            if not p.is_empty:
                polygons.append(p)

    if not polygons:
        return ObsX, ObsY

    total_cells = Nx * Ny
    if total_cells > 0:
        sys.stdout.write("\r  Calculating subgrid obstructions...   0.0%")
        sys.stdout.flush()

    # Build STRtree spatial index for fast candidate polygon lookups
    tree = STRtree(polygons)

    # Compute cell corners, widths, and heights for all cells
    polygons_cell, widths, heights = compute_all_corners(x, y)

    # Identify wet cells
    wet_k, wet_j = np.where(mask != 0)
    num_wet = len(wet_k)

    if num_wet > 0:
        wet_coords = polygons_cell[wet_k, wet_j]

        batch_size = max(1000, total_cells // 50)
        num_batches = (num_wet + batch_size - 1) // batch_size
        processed = 0
        last_pct = -1.0

        for b in range(num_batches):
            b_start = b * batch_size
            b_end = min(num_wet, (b + 1) * batch_size)
            batch_coords = wet_coords[b_start:b_end]
            batch_cell_polys = shapely.polygons(batch_coords)

            cell_idxs, poly_idxs = tree.query(batch_cell_polys, predicate="intersects")

            if len(cell_idxs) > 0:
                unique_batch_cells = np.unique(cell_idxs)
                for u_idx in unique_batch_cells:
                    global_u_idx = b_start + u_idx
                    k = wet_k[global_u_idx]
                    j = wet_j[global_u_idx]
                    cell_poly = batch_cell_polys[u_idx]
                    hgt = heights[k, j]
                    wdth = widths[k, j]

                    matched_poly_idxs = poly_idxs[cell_idxs == u_idx]

                    ObsX_val = 0.0
                    ObsY_val = 0.0

                    for p_idx in matched_poly_idxs:
                        poly = polygons[p_idx]
                        inter = cell_poly.intersection(poly)
                        if not inter.is_empty:
                            minx, miny, maxx, maxy = inter.bounds
                            if hgt > 0:
                                ObsX_val = max(ObsX_val, (maxy - miny) / hgt)
                            if wdth > 0:
                                ObsY_val = max(ObsY_val, (maxx - minx) / wdth)

                    ObsX[k, j] = min(1.0, max(0.0, ObsX_val))
                    ObsY[k, j] = min(1.0, max(0.0, ObsY_val))

            processed += (b_end - b_start)
            pct = (processed / total_cells) * 100.0
            curr_pct = round(pct, 1)
            if curr_pct != last_pct:
                last_pct = curr_pct
                sys.stdout.write(f"\r  Calculating subgrid obstructions... {pct:5.1f}%")
                sys.stdout.flush()

    if total_cells > 0:
        sys.stdout.write("\r  Calculating subgrid obstructions... 100.0%\n")
        sys.stdout.flush()

    # Zero out obstructions adjacent to dry cells to prevent spurious attenuation
    dry = (mask == 0)
    ObsX[:, :-1][dry[:, 1:]] = 0.0
    ObsX[:, 1:][dry[:, :-1]] = 0.0
    ObsY[:-1, :][dry[1:, :]] = 0.0
    ObsY[1:, :][dry[:-1, :]] = 0.0

    return ObsX, ObsY
