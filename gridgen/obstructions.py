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
# Converted from create_obstr.m originally authored by NOAA/NCEP
# (Arun Chawla).

"""Subgrid obstruction calculation routines for WAVEWATCH III (WW3) / WAVEWATCH IV (WW4)."""

from __future__ import annotations

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
    """Generate subgrid obstruction grids sx and sy.

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
    sx, sy : np.ndarray
        2D obstruction arrays in x and y directions of shape (Ny, Nx).
        Values range from 0.0 (no obstruction) to 1.0 (full obstruction).
    """
    Ny, Nx = x.shape
    sx = np.zeros((Ny, Nx), dtype=np.float64)
    sy = np.zeros((Ny, Nx), dtype=np.float64)

    if not bound_list:
        return sx, sy

    polygons = []
    for b in bound_list:
        if "polygon" in b and b["polygon"] is not None:
            p = b["polygon"]
        else:
            bx = np.asarray(b["x"], dtype=np.float64)
            by = np.asarray(b["y"], dtype=np.float64)
            p = Polygon(np.column_stack((bx, by)))
        polygons.append(p)

    for j in range(Nx):
        for k in range(Ny):
            if mask[k, j] == 0:
                continue

            c1, c2, c3, c4, wdth, hgt = compute_cellcorner(x, y, j, k)
            cell_poly = Polygon([c4, c1, c2, c3, c4])

            # Calculate intersection ratio along x and y edges
            # sx: obstruction across x-boundary (i-index)
            # sy: obstruction across y-boundary (j-index)
            sx_val = 0.0
            sy_val = 0.0

            for poly in polygons:
                if cell_poly.intersects(poly):
                    inter = cell_poly.intersection(poly)
                    if not inter.is_empty:
                        # Estimate projection along height and width
                        minx, miny, maxx, maxy = inter.bounds
                        if hgt > 0:
                            sx_val = max(sx_val, (maxy - miny) / hgt)
                        if wdth > 0:
                            sy_val = max(sy_val, (maxx - minx) / wdth)

            sx[k, j] = min(1.0, max(0.0, sx_val))
            sy[k, j] = min(1.0, max(0.0, sy_val))

    # Zero out obstructions adjacent to dry cells to prevent spurious attenuation
    for j in range(Nx):
        for k in range(Ny):
            if mask[k, j] == 1:
                if j < Nx - 1 and mask[k, j + 1] == 0:
                    sx[k, j] = 0.0
                if j > 0 and mask[k, j - 1] == 0:
                    sx[k, j] = 0.0
                if k < Ny - 1 and mask[k + 1, j] == 0:
                    sy[k, j] = 0.0
                if k > 0 and mask[k - 1, j] == 0:
                    sy[k, j] = 0.0

    return sx, sy
