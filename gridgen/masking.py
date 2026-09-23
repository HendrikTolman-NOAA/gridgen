# WAVEWATCH IV (WW4) Gridgen Package
#
# Copyright 2026 National Weather Service (NWS), NOAA. All rights reserved.
# NWS often uses Generative AI (GenAI) for code development and refactoring.
# Whenever GenAI is used, NWS requires a full human review of code before it
# is added to its repositories.
#
# @author Aldgisl (Agentic AI)
# @author Hendrik Tolman
# @date Initial: 2026-05-20
# @date Update: 2026-05-20
#
# Code Heritage:
# Converted from clean_mask.m, remove_lake.m, compute_boundary.m, split_boundary.m
# originally authored by NOAA/NCEP (Arun Chawla).

"""Mask processing and boundary utilities for WAVEWATCH IV."""

from typing import Any

import numpy as np
from shapely.geometry import Point, Polygon, box
from shapely.strtree import STRtree

from .geometry import compute_cellcorner


def compute_boundary(
    coord: tuple[float, float, float, float],
    bound_list: list[dict[str, Any]],
    bflg: int = 1,
) -> tuple[list[dict[str, Any]], int]:
    """Extract boundary polygons within the specified domain coordinate bounds.

    Parameters
    ----------
    coord : Tuple[float, float, float, float]
        (lat_start, lon_start, lat_end, lon_end)
    bound_list : List[Dict[str, Any]]
        List of boundary polygon dictionaries containing 'x', 'y', 'level', etc.
    bflg : int
        Boundary flag filter (1 = land).

    Returns
    -------
    bound_ingrid : List[Dict[str, Any]]
        List of boundary polygon dictionaries inside domain.
    Nb : int
        Number of boundary polygons found inside domain.
    """
    lat_start, lon_start, lat_end, lon_end = coord
    domain_poly = box(lon_start, lat_start, lon_end, lat_end)

    bound_ingrid = []

    for b in bound_list:
        level = b.get("level", 1)
        if level != bflg:
            continue

        bx = np.asarray(b["x"], dtype=np.float64)
        by = np.asarray(b["y"], dtype=np.float64)

        if len(bx) < 3:
            continue

        west, east = float(np.min(bx)), float(np.max(bx))
        south, north = float(np.min(by)), float(np.max(by))

        if west > lon_end or east < lon_start or south > lat_end or north < lat_start:
            continue

        poly_coords = np.column_stack((bx, by))
        poly = Polygon(poly_coords)

        if not poly.is_valid:
            poly = poly.buffer(0)

        if domain_poly.contains(poly):
            bound_ingrid.append(
                {
                    "x": bx,
                    "y": by,
                    "n": len(bx),
                    "west": west,
                    "east": east,
                    "south": south,
                    "north": north,
                    "width": east - west,
                    "height": north - south,
                    "level": level,
                    "polygon": poly,
                }
            )
        elif domain_poly.intersects(poly):
            inter = domain_poly.intersection(poly)
            geoms = inter.geoms if hasattr(inter, "geoms") else [inter]
            for g in geoms:
                if isinstance(g, Polygon) and not g.is_empty:
                    ext_coords = np.array(g.exterior.coords)
                    if len(ext_coords) >= 3:
                        gx = ext_coords[:, 0]
                        gy = ext_coords[:, 1]
                        g_west, g_east = float(np.min(gx)), float(np.max(gx))
                        g_south, g_north = float(np.min(gy)), float(np.max(gy))
                        bound_ingrid.append(
                            {
                                "x": gx,
                                "y": gy,
                                "n": len(gx),
                                "west": g_west,
                                "east": g_east,
                                "south": g_south,
                                "north": g_north,
                                "width": g_east - g_west,
                                "height": g_north - g_south,
                                "level": level,
                                "polygon": g,
                            }
                        )

    return bound_ingrid, len(bound_ingrid)


def split_boundary(
    bound_list: list[dict[str, Any]], lim: float
) -> list[dict[str, Any]]:
    """Split large boundary polygons into smaller sub-polygons.

    Parameters
    ----------
    bound_list : List[Dict[str, Any]]
        List of boundary polygon dictionaries.
    lim : float
        Maximum dimension limit for splitting.

    Returns
    -------
    List[Dict[str, Any]]
        List of split boundary polygon dictionaries.
    """
    result = []
    for b in bound_list:
        w = b.get("width", float(np.max(b["x"]) - np.min(b["x"])))
        h = b.get("height", float(np.max(b["y"]) - np.min(b["y"])))

        if w > lim or h > lim:
            west = float(b["west"])
            east = float(b["east"])
            south = float(b["south"])
            north = float(b["north"])

            x_axis = np.arange(west, east + lim, lim)
            y_axis = np.arange(south, north + lim, lim)

            for lx in range(len(x_axis) - 1):
                for ly in range(len(y_axis) - 1):
                    sub_coord = (
                        y_axis[ly],
                        x_axis[lx],
                        y_axis[ly + 1],
                        x_axis[lx + 1],
                    )
                    sub_b, _ = compute_boundary(
                        sub_coord, [b], bflg=b.get("level", 1)
                    )
                    result.extend(sub_b)
        else:
            result.append(b)

    return result


def clean_mask(
    x: np.ndarray,
    y: np.ndarray,
    mask: np.ndarray,
    bound_ingrid: list[dict[str, Any]],
    lim: float = 0.5,
    offset: float = 0.0,
) -> np.ndarray:
    """Clean land/sea mask using boundary polygons.

    Parameters
    ----------
    x : np.ndarray
        2D longitude array of shape (Ny, Nx).
    y : np.ndarray
        2D latitude array of shape (Ny, Nx).
    mask : np.ndarray
        Initial 2D mask array (1 = wet, 0 = dry).
    bound_ingrid : List[Dict[str, Any]]
        Boundary polygons inside the grid domain.
    lim : float
        Fraction limit of cell area inside boundary required to mark cell dry.
    offset : float
        Buffer distance around boundaries.

    Returns
    -------
    clean_m : np.ndarray
        Cleaned 2D land/sea mask array.
    """
    Ny, Nx = x.shape
    clean_m = np.copy(mask)

    if not bound_ingrid:
        return clean_m

    polygons = []
    for b in bound_ingrid:
        if "polygon" in b and b["polygon"] is not None:
            p = b["polygon"]
        else:
            bx = np.asarray(b["x"], dtype=np.float64)
            by = np.asarray(b["y"], dtype=np.float64)
            p = Polygon(np.column_stack((bx, by)))
        if offset > 0:
            p = p.buffer(offset)
        if not p.is_valid:
            p = p.buffer(0)
        polygons.append(p)

    tree = STRtree(polygons)

    for j in range(Nx):
        for k in range(Ny):
            if clean_m[k, j] == 1:
                c1, c2, c3, c4, _, _ = compute_cellcorner(x, y, j, k)
                cell_poly = Polygon([c4, c1, c2, c3, c4])

                matching_indices = tree.query(cell_poly, predicate="intersects")
                if len(matching_indices) == 0:
                    continue

                xmin, ymin, xmax, ymax = cell_poly.bounds
                xtt = np.linspace(xmin, xmax, 6)
                ytt = np.linspace(ymin, ymax, 6)
                xtt2, ytt2 = np.meshgrid(xtt, ytt)

                pts_in_cell = []
                for px_val, py_val in zip(xtt2.ravel(), ytt2.ravel()):
                    pt = Point(px_val, py_val)
                    if cell_poly.contains(pt):
                        pts_in_cell.append(pt)

                if not pts_in_cell:
                    continue

                pts_in_bound = 0
                for pt in pts_in_cell:
                    for idx in matching_indices:
                        if polygons[idx].contains(pt):
                            pts_in_bound += 1
                            break

                overlap_ratio = pts_in_bound / len(pts_in_cell)
                if overlap_ratio >= lim:
                    clean_m[k, j] = 0

    return clean_m


def remove_lake(
    mask: np.ndarray, lake_tol: float = -1, igl: int = 0
) -> tuple[np.ndarray, np.ndarray]:
    """Group wet cells into independent water bodies and remove isolated lakes.

    Parameters
    ----------
    mask : np.ndarray
        2D land/sea mask (1 = wet, 0 = dry).
    lake_tol : float
        Tolerance for lake removal:
        - If > 0: remove water bodies with fewer than `lake_tol` cells.
        - If < 0: keep only the single largest water body.
        - If = 0: no removal.
    igl : int
        1 for global grid (wrap-around in x), 0 for regional grid.

    Returns
    -------
    mask_mod : np.ndarray
        Modified 2D land/sea mask array.
    mask_map : np.ndarray
        2D array with -1 for dry cells and unique water body IDs for wet cells.
    """
    Ny, Nx = mask.shape
    mask_map = np.full((Ny, Nx), -1, dtype=int)
    mask_map[mask == 1] = 0

    last_mask = 0
    body_sizes = {}

    unmarked = np.argwhere(mask_map == 0)

    for row, col in unmarked:
        if mask_map[row, col] != 0:
            continue

        last_mask += 1
        queue = [(row, col)]
        mask_map[row, col] = last_mask
        cell_count = 0

        while queue:
            r, c = queue.pop(0)
            cell_count += 1

            prev_c = Nx - 1 if (c == 0 and igl == 1) else c - 1
            next_c = 0 if (c == Nx - 1 and igl == 1) else c + 1
            prev_r = max(0, r - 1)
            next_r = min(Ny - 1, r + 1)

            neighbors = []
            if prev_c >= 0 and mask_map[r, prev_c] == 0:
                neighbors.append((r, prev_c))
            if next_c < Nx and mask_map[r, next_c] == 0:
                neighbors.append((r, next_c))
            if prev_r != r and mask_map[prev_r, c] == 0:
                neighbors.append((prev_r, c))
            if next_r != r and mask_map[next_r, c] == 0:
                neighbors.append((next_r, c))

            for nr, nc in neighbors:
                mask_map[nr, nc] = last_mask
                queue.append((nr, nc))

        body_sizes[last_mask] = cell_count

    mask_mod = np.copy(mask)

    if lake_tol != 0 and body_sizes:
        if lake_tol < 0:
            largest_id = max(body_sizes, key=body_sizes.get)
            for body_id in body_sizes:
                if body_id != largest_id:
                    mask_mod[mask_map == body_id] = 0
        else:
            for body_id, size in body_sizes.items():
                if size < lake_tol:
                    mask_mod[mask_map == body_id] = 0

    return mask_mod, mask_map
