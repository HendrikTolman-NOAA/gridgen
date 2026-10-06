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
# Converted from compute_cellcorner.m originally authored by NOAA/NCEP
# (Arun Chawla).

"""Geometric utilities for WAVEWATCH III (WW3) / WAVEWATCH IV (WW4) grid generation."""

from __future__ import annotations

import numpy as np


def compute_cellcorner(
    x: np.ndarray, y: np.ndarray, j: int, k: int
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, float, float]:
    """Compute 4 corner coordinates, width, and height of a specific grid cell (k, j).

    Parameters
    ----------------
    x : np.ndarray
        2D array of longitudes with shape (Ny, Nx).
    y : np.ndarray
        2D array of latitudes with shape (Ny, Nx).
    j : int
        0-based column index (x dimension).
    k : int
        0-based row index (y dimension).

    Returns
    -------
    c1, c2, c3, c4 : np.ndarray
        2-element 1D arrays [lon, lat] for cell corners 1 through 4.
        Orientation: c3 (top-left), c2 (top-right), c4 (bottom-left), c1 (bottom-right).
    wdth : float
        Cell width in degrees / grid units.
    hgt : float
        Cell height in degrees / grid units.
    """
    Ny, Nx = x.shape
    x0 = float(x[k, j])
    y0 = float(y[k, j])

    c1 = np.zeros(2, dtype=np.float64)
    c2 = np.zeros(2, dtype=np.float64)
    c3 = np.zeros(2, dtype=np.float64)
    c4 = np.zeros(2, dtype=np.float64)

    def _unwrap_lon(xt: float) -> float:
        if abs(xt - x0) > 270.0:
            return xt - 360.0 * np.sign(xt - x0)
        return xt

    if 0 < j < Nx - 1 and 0 < k < Ny - 1:
        # Internal points
        xt1 = _unwrap_lon(float(x[k - 1, j + 1]))
        c1[0] = 0.5 * (xt1 + x0)
        c1[1] = 0.5 * (float(y[k - 1, j + 1]) + y0)

        xt2 = _unwrap_lon(float(x[k + 1, j + 1]))
        c2[0] = 0.5 * (xt2 + x0)
        c2[1] = 0.5 * (float(y[k + 1, j + 1]) + y0)

        xt3 = _unwrap_lon(float(x[k + 1, j - 1]))
        c3[0] = 0.5 * (xt3 + x0)
        c3[1] = 0.5 * (float(y[k + 1, j - 1]) + y0)

        xt4 = _unwrap_lon(float(x[k - 1, j - 1]))
        c4[0] = 0.5 * (xt4 + x0)
        c4[1] = 0.5 * (float(y[k - 1, j - 1]) + y0)
    else:
        if j == 0:  # Left edge
            if k == 0:
                xt2 = _unwrap_lon(float(x[k + 1, j + 1]))
                c2[0] = 0.5 * (xt2 + x0)
                c2[1] = 0.5 * (float(y[k + 1, j + 1]) + y0)
                c4[0] = 2.0 * x0 - c2[0]
                c4[1] = 2.0 * y0 - c2[1]
                c3[0] = x0 - (c2[1] - y0)
                c3[1] = y0 + (c2[0] - x0)
                c1[0] = 2.0 * x0 - c3[0]
                c1[1] = 2.0 * y0 - c3[1]
            elif k == Ny - 1:
                xt1 = _unwrap_lon(float(x[k - 1, j + 1]))
                c1[0] = 0.5 * (xt1 + x0)
                c1[1] = 0.5 * (float(y[k - 1, j + 1]) + y0)
                c3[0] = 2.0 * x0 - c1[0]
                c3[1] = 2.0 * y0 - c1[1]
                c2[0] = x0 - (y0 - c1[1])
                c2[1] = y0 + (x0 - c1[0])
                c4[0] = 2.0 * x0 - c2[0]
                c4[1] = 2.0 * y0 - c2[1]
            else:
                xt1 = _unwrap_lon(float(x[k - 1, j + 1]))
                c1[0] = 0.5 * (xt1 + x0)
                c1[1] = 0.5 * (float(y[k - 1, j + 1]) + y0)
                xt2 = _unwrap_lon(float(x[k + 1, j + 1]))
                c2[0] = 0.5 * (xt2 + x0)
                c2[1] = 0.5 * (float(y[k + 1, j + 1]) + y0)
                c3[0] = 2.0 * x0 - c1[0]
                c3[1] = 2.0 * y0 - c1[1]
                c4[0] = 2.0 * x0 - c2[0]
                c4[1] = 2.0 * y0 - c2[1]
        elif j == Nx - 1:  # Right edge
            if k == 0:
                xt3 = _unwrap_lon(float(x[k + 1, j - 1]))
                c3[0] = 0.5 * (xt3 + x0)
                c3[1] = 0.5 * (float(y[k + 1, j - 1]) + y0)
                c2[0] = x0 - (c3[1] - y0)
                c2[1] = y0 + (c3[0] - x0)
                c1[0] = 2.0 * x0 - c3[0]
                c1[1] = 2.0 * y0 - c3[1]
                c4[0] = 2.0 * x0 - c2[0]
                c4[1] = 2.0 * y0 - c2[1]
            elif k == Ny - 1:
                xt4 = _unwrap_lon(float(x[k - 1, j - 1]))
                c4[0] = 0.5 * (xt4 + x0)
                c4[1] = 0.5 * (float(y[k - 1, j - 1]) + y0)
                c3[0] = x0 - (c4[1] - y0)
                c3[1] = y0 + (c4[0] - x0)
                c1[0] = 2.0 * x0 - c3[0]
                c1[1] = 2.0 * y0 - c3[1]
                c2[0] = 2.0 * x0 - c4[0]
                c2[1] = 2.0 * y0 - c4[1]
            else:
                xt3 = _unwrap_lon(float(x[k + 1, j - 1]))
                c3[0] = 0.5 * (xt3 + x0)
                c3[1] = 0.5 * (float(y[k + 1, j - 1]) + y0)
                xt4 = _unwrap_lon(float(x[k - 1, j - 1]))
                c4[0] = 0.5 * (xt4 + x0)
                c4[1] = 0.5 * (float(y[k - 1, j - 1]) + y0)
                c1[0] = 2.0 * x0 - c3[0]
                c1[1] = 2.0 * y0 - c3[1]
                c2[0] = 2.0 * x0 - c4[0]
                c2[1] = 2.0 * y0 - c4[1]
        elif k == 0:  # Bottom edge
            xt2 = _unwrap_lon(float(x[k + 1, j + 1]))
            c2[0] = 0.5 * (xt2 + x0)
            c2[1] = 0.5 * (float(y[k + 1, j + 1]) + y0)
            xt3 = _unwrap_lon(float(x[k + 1, j - 1]))
            c3[0] = 0.5 * (xt3 + x0)
            c3[1] = 0.5 * (float(y[k + 1, j - 1]) + y0)
            c4[0] = 2.0 * x0 - c2[0]
            c4[1] = 2.0 * y0 - c2[1]
            c1[0] = 2.0 * x0 - c3[0]
            c1[1] = 2.0 * y0 - c3[1]
        else:  # Top edge (k == Ny - 1)
            xt4 = _unwrap_lon(float(x[k - 1, j - 1]))
            c4[0] = 0.5 * (xt4 + x0)
            c4[1] = 0.5 * (float(y[k - 1, j - 1]) + y0)
            xt1 = _unwrap_lon(float(x[k - 1, j + 1]))
            c1[0] = 0.5 * (xt1 + x0)
            c1[1] = 0.5 * (float(y[k - 1, j + 1]) + y0)
            c2[0] = 2.0 * x0 - c4[0]
            c2[1] = 2.0 * y0 - c4[1]
            c3[0] = 2.0 * x0 - c1[0]
            c3[1] = 2.0 * y0 - c1[1]

    wdth = float(np.sqrt((c1[0] - c4[0]) ** 2 + (c1[1] - c4[1]) ** 2))
    hgt = float(np.sqrt((c2[0] - c1[0]) ** 2 + (c2[1] - c1[1]) ** 2))

    return c1, c2, c3, c4, wdth, hgt


def compute_all_corners(
    x: np.ndarray, y: np.ndarray
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Compute polygon corners, widths, and heights for all grid cells.

    Parameters
    ----------
    x : np.ndarray
        2D array of longitudes with shape (Ny, Nx).
    y : np.ndarray
        2D array of latitudes with shape (Ny, Nx).

    Returns
    -------
    polygons : np.ndarray
        Array of shape (Ny, Nx, 5, 2) where each cell has 5 vertices [lon, lat]
        (closed polygon: c4, c1, c2, c3, c4).
    widths : np.ndarray
        2D array of cell widths with shape (Ny, Nx).
    heights : np.ndarray
        2D array of cell heights with shape (Ny, Nx).
    """
    Ny, Nx = x.shape
    polygons = np.zeros((Ny, Nx, 5, 2), dtype=np.float64)
    widths = np.zeros((Ny, Nx), dtype=np.float64)
    heights = np.zeros((Ny, Nx), dtype=np.float64)

    for j in range(Nx):
        for k in range(Ny):
            c1, c2, c3, c4, w, h = compute_cellcorner(x, y, j, k)
            polygons[k, j, 0] = c4
            polygons[k, j, 1] = c1
            polygons[k, j, 2] = c2
            polygons[k, j, 3] = c3
            polygons[k, j, 4] = c4
            widths[k, j] = w
            heights[k, j] = h

    return polygons, widths, heights
