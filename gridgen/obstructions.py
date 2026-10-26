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
# @date Latest Update: 2026-10-20
#
# Code Heritage:
# Converted from create_obstr.m originally authored by NOAA/NCEP
# (Arun Chawla).

"""Subgrid obstruction calculation routines for WAVEWATCH III (WW3) / WAVEWATCH IV (WW4)."""

from __future__ import annotations

import sys
from typing import Any

import numpy as np
from shapely.geometry import Polygon

from .geometry import compute_cellcorner


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
        bx = np.asarray(b["x"], dtype=np.float64)
        by = np.asarray(b["y"], dtype=np.float64)
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
    processed = 0
    last_pct = -1.0

    for j in range(Nx):
        for k in range(Ny):
            processed += 1
            if total_cells > 0:
                pct = (processed / total_cells) * 100.0
                curr_pct = round(pct, 1)
                if curr_pct != last_pct or processed == total_cells:
                    last_pct = curr_pct
                    sys.stdout.write(f"\r  Calculating subgrid obstructions... {pct:5.1f}%")
                    sys.stdout.flush()

            if mask[k, j] == 0:
                continue

            c1, c2, c3, c4, wdth, hgt = compute_cellcorner(x, y, j, k)
            cell_poly = Polygon([c4, c1, c2, c3, c4])

            # Calculate intersection ratio along x and y edges
            # ObsX: obstruction across x-boundary (i-index)
            # ObsY: obstruction across y-boundary (j-index)
            ObsX_val = 0.0
            ObsY_val = 0.0

            for poly in polygons:
                if cell_poly.intersects(poly):
                    inter = cell_poly.intersection(poly)
                    if not inter.is_empty:
                        # Estimate projection along height and width
                        minx, miny, maxx, maxy = inter.bounds
                        if hgt > 0:
                            ObsX_val = max(ObsX_val, (maxy - miny) / hgt)
                        if wdth > 0:
                            ObsY_val = max(ObsY_val, (maxx - minx) / wdth)

            ObsX[k, j] = min(1.0, max(0.0, ObsX_val))
            ObsY[k, j] = min(1.0, max(0.0, ObsY_val))

    if total_cells > 0:
        sys.stdout.write("\n")
        sys.stdout.flush()

    # Zero out obstructions across cell faces bordering dry cells to prevent spurious attenuation.
    # ObsX[k, j] is defined at the East face (i-boundary between (k, j) and (k, j+1)).
    # ObsY[k, j] is defined at the North face (j-boundary between (k, j) and (k+1, j)).
    dx = float(abs(x[0, 1] - x[0, 0])) if x.ndim == 2 and x.shape[1] > 1 else 1.0
    is_global_lon = (Nx * dx >= 355.0) or (float(np.max(x) - np.min(x)) >= 355.0)

    for j in range(Nx):
        for k in range(Ny):
            if mask[k, j] == 1:
                next_j = (j + 1) % Nx if (j == Nx - 1 and is_global_lon) else j + 1
                if next_j < Nx and mask[k, next_j] == 0:
                    ObsX[k, j] = 0.0
                if k < Ny - 1 and mask[k + 1, j] == 0:
                    ObsY[k, j] = 0.0

    return ObsX, ObsY
