# WAVEWATCH III (WW3) / WAVEWATCH IV (WW4) Gridgen Package
#
# Copyright 2026 National Weather Service (NWS), NOAA. All rights reserved.
# NWS often uses Generative AI (GenAI) for code development and refactoring.
# Whenever GenAI is used, NWS requires a full human review of code before it
# is added to its repositories.
#
# @author Aldgisl (Agentic AI), Hendrik Tolman
# @author Jules (Agentic AI) (contributor)
# @date Initial: 2026-09-22
# @date Latest Update: 2026-10-06
#
# Code Heritage:
# Converted from clean_mask.m, remove_lake.m, compute_boundary.m, split_boundary.m,
# modify_mask.m, and optional_bound.m originally authored by NOAA/NCEP (Arun Chawla).

"""Mask processing and boundary utilities for WAVEWATCH III (WW3) / WAVEWATCH IV (WW4)."""

from __future__ import annotations

import os
from typing import Any

import numpy as np
import scipy.io as sio
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
                    sub_b, _ = compute_boundary(sub_coord, [b], bflg=b.get("level", 1))
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


def define_boundary_points(
    mask: np.ndarray,
    lon: np.ndarray,
    lat: np.ndarray,
    base_mask: np.ndarray | None = None,
    base_lon: np.ndarray | None = None,
    base_lat: np.ndarray | None = None,
    igl: int = 0,
    active_poly: tuple[np.ndarray, np.ndarray] | None = None,
) -> np.ndarray:
    """Define input boundary points (mask value 2) in regional / nested grids.

    Ported from legacy MATLAB modify_mask.m function.

    Parameters
    ----------
    mask : np.ndarray
        2D land/sea mask array (0 = land, 1 = wet).
    lon : np.ndarray
        2D longitude coordinates array of shape (Ny, Nx).
    lat : np.ndarray
        2D latitude coordinates array of shape (Ny, Nx).
    base_mask : Optional[np.ndarray]
        2D mask array for parent/base grid (used for nesting reconciliation).
    base_lon : Optional[np.ndarray]
        2D longitude coordinates array for parent/base grid.
    base_lat : Optional[np.ndarray]
        2D latitude coordinates array for parent/base grid.
    igl : int
        1 if base grid is global (wrap-around lon), 0 if regional.
    active_poly : Optional[Tuple[np.ndarray, np.ndarray]]
        Optional tuple (px, py) of boundary coordinates defining active computation.

    Returns
    -------
    m_new : np.ndarray
        Modified 2D mask array with values:
        0 = Land/Dry cell
        1 = Active wet cell
        2 = Input boundary cell
        3 = Excluded/Inactive cell
    """
    Ny, Nx = mask.shape
    m_new = np.copy(mask)

    # 1. Apply active computation polygon if provided
    if active_poly is not None:
        px, py = active_poly
        poly_coords = np.column_stack((px, py))
        comp_poly = Polygon(poly_coords)

        for k in range(Ny):
            for j in range(Nx):
                pt = Point(float(lon[k, j]), float(lat[k, j]))
                if not comp_poly.contains(pt):
                    m_new[k, j] = 3

    # 2. Flag outer domain edges as input boundary cells (value 2)
    for j in range(Ny):
        if m_new[j, 0] == 1:
            m_new[j, 0] = 2
        if m_new[j, Nx - 1] == 1:
            m_new[j, Nx - 1] = 2

    for k in range(Nx):
        if m_new[0, k] == 1:
            m_new[0, k] = 2
        if m_new[Ny - 1, k] == 1:
            m_new[Ny - 1, k] = 2

    # 3. Flag cells adjacent to inactive cells (value 3) as boundary cells (value 2)
    inactive_indices = np.argwhere(m_new == 3)
    for r, c in inactive_indices:
        ny_down = max(0, r - 1)
        ny_up = min(Ny - 1, r + 1)
        nx_left = max(0, c - 1)
        nx_right = min(Nx - 1, c + 1)

        found_wet = False
        if (
            m_new[r, nx_left] == 1
            or m_new[r, nx_right] == 1
            or m_new[ny_down, c] == 1
            or m_new[ny_up, c] == 1
        ):
            found_wet = True

        if found_wet:
            m_new[r, c] = 2

    # 4. Reconcile boundary cells with parent/base grid if base grid provided
    if base_mask is not None and base_lon is not None and base_lat is not None:
        boundary_indices = np.argwhere(m_new == 2)
        Nyb, Nxb = base_lon.shape

        dxb = float(abs(base_lon[0, 1] - base_lon[0, 0])) if Nxb > 1 else 1.0
        dyb = float(abs(base_lat[1, 0] - base_lat[0, 0])) if Nyb > 1 else 1.0

        lonb_min = float(base_lon[0, 0])
        latb_min = float(base_lat[0, 0])

        for r, c in boundary_indices:
            x_val = float(lon[r, c])
            y_val = float(lat[r, c])

            ry = (y_val - latb_min) / dyb
            jy = int(np.floor(ry))
            ry = ry - jy

            if jy < 0 or jy >= Nyb - 1:
                m_new[r, c] = 3
                continue

            rx = (x_val - lonb_min) / dxb
            jx = int(np.floor(rx))
            rx = rx - jx

            if igl != 1:
                if jx < 0 or jx >= Nxb - 1:
                    m_new[r, c] = 3
                    continue
            else:
                jx = jx % Nxb

            jx1 = jx
            jx2 = (jx + 1) % Nxb if igl == 1 else jx + 1
            jy1 = jy
            jy2 = jy + 1

            if jx2 >= Nxb or jy2 >= Nyb:
                m_new[r, c] = 3
                continue

            b11 = abs(base_mask[jy1, jx1]) in (1, 2) or (1.0 - rx) * (1.0 - ry) < 0.05
            b12 = abs(base_mask[jy1, jx2]) in (1, 2) or rx * (1.0 - ry) < 0.05
            b21 = abs(base_mask[jy2, jx1]) in (1, 2) or (1.0 - rx) * ry < 0.05
            b22 = abs(base_mask[jy2, jx2]) in (1, 2) or rx * (1.0 - ry) < 0.05

            if not (b11 and b12 and b21 and b22):
                m_new[r, c] = 3

    return m_new


def load_user_polygons(
    ref_dir: str = "reference_data",
    flag_file: str | None = None,
    mat_filename: str = "optional_coastal_polygons.mat",
) -> list[dict[str, Any]]:
    """Load user-defined optional coastal polygons filtered by a flag control file.

    Ported from legacy MATLAB optional_bound.m function.

    Parameters
    ----------
    ref_dir : str
        Directory containing optional coastal polygon MAT datasets.
    flag_file : Optional[str]
        Path to text file containing binary switches (0 = off, 1 = on) per polygon.
    mat_filename : str
        Filename of MAT file containing user coastal polygons.

    Returns
    -------
    active_polygons : List[Dict[str, Any]]
        List of active user boundary polygon dictionaries.
    """
    mat_path = os.path.join(ref_dir, mat_filename)
    if not os.path.exists(mat_path):
        return []

    mat_data = sio.loadmat(mat_path, squeeze_me=True, struct_as_record=False)
    if "user_bound" not in mat_data:
        return []

    user_bound = mat_data["user_bound"]
    if not isinstance(user_bound, np.ndarray):
        user_bound = np.array([user_bound])

    switches = []
    if flag_file and os.path.exists(flag_file):
        with open(flag_file) as f:
            for line in f:
                line_str = line.strip()
                if not line_str or line_str.startswith("#"):
                    continue
                parts = line_str.split()
                if len(parts) >= 2:
                    switches.append(int(parts[1]))
                elif len(parts) == 1:
                    switches.append(int(parts[0]))

    if not switches:
        switches = [1] * len(user_bound)

    active_polygons = []
    for idx, bound_obj in enumerate(user_bound):
        if idx >= len(switches) or switches[idx] != 1:
            continue

        bx = np.asarray(getattr(bound_obj, "x", []), dtype=np.float64)
        by = np.asarray(getattr(bound_obj, "y", []), dtype=np.float64)
        if len(bx) < 3:
            continue

        west, east = float(np.min(bx)), float(np.max(bx))
        south, north = float(np.min(by)), float(np.max(by))
        poly = Polygon(np.column_stack((bx, by)))
        if not poly.is_valid:
            poly = poly.buffer(0)

        active_polygons.append(
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
                "level": int(getattr(bound_obj, "level", 1)),
                "polygon": poly,
            }
        )

    return active_polygons


# Backward compatibility alias
modify_mask = define_boundary_points
