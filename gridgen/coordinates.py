# WAVEWATCH III (WW3) / WAVEWATCH IV (WW4) Gridgen Package
#
# Copyright 2026 National Weather Service (NWS), NOAA. All rights reserved.
# NWS often uses Generative AI (GenAI) for code development and refactoring.
# Whenever GenAI is used, NWS requires a full human review of code before it
# is added to its repositories.
#
# @author Aldgisl (Agentic AI), Hendrik Tolman
# @author Jules (Agentic AI) (contributor)
# @date Initial: 2026-10-06
# @date Latest Update: 2026-10-06

"""Grid coordinate generation module for WAVEWATCH III (WW3) / WAVEWATCH IV (WW4).

Provides 2D coordinate generation routines for regular, polar stereographic,
Mercator, and rotated pole grid geometries.
"""

from __future__ import annotations

import numpy as np


def create_regular_grid(
    lon_start: float = 140.0,
    lon_end: float = 160.0,
    lat_start: float = 44.0,
    lat_end: float = 54.0,
    dx: float = 0.25,
    dy: float = 0.25,
    nx: int | None = None,
    ny: int | None = None,
) -> tuple[np.ndarray, np.ndarray]:
    """Generate 2D arrays of longitude and latitude for a regular grid.

    Parameters
    ----------
    lon_start : float
        Minimum longitude in degrees.
    lon_end : float
        Maximum longitude in degrees.
    lat_start : float
        Minimum latitude in degrees.
    lat_end : float
        Maximum latitude in degrees.
    dx : float
        Longitude resolution increment in degrees (used if nx is None).
    dy : float
        Latitude resolution increment in degrees (used if ny is None).
    nx : int | None
        Number of longitude grid points (overrides dx if provided).
    ny : int | None
        Number of latitude grid points (overrides dy if provided).

    Returns
    -------
    lon : np.ndarray
        2D longitude grid array of shape (Ny, Nx).
    lat : np.ndarray
        2D latitude grid array of shape (Ny, Nx).
    """
    if nx is not None:
        lon1d = np.linspace(lon_start, lon_end, nx)
    else:
        lon1d = np.arange(lon_start, lon_end + dx * 0.5, dx)

    if ny is not None:
        lat1d = np.linspace(lat_start, lat_end, ny)
    else:
        lat1d = np.arange(lat_start, lat_end + dy * 0.5, dy)

    lon, lat = np.meshgrid(lon1d, lat1d)
    return lon, lat


def create_polar_stereographic_grid(
    center_lon: float = 0.0,
    center_lat: float = 90.0,
    extent_km: float = 2000.0,
    resolution_km: float = 50.0,
    nx: int | None = None,
    ny: int | None = None,
) -> tuple[np.ndarray, np.ndarray]:
    """Generate 2D geographic coordinates for a polar stereographic grid.

    Parameters
    ----------
    center_lon : float
        Central meridian of projection in degrees.
    center_lat : float
        Central latitude of projection (+90 for North Pole, -90 for South Pole).
    extent_km : float
        Half-width extent of domain in kilometers.
    resolution_km : float
        Grid spacing in kilometers.
    nx : int | None
        Number of grid points in x direction.
    ny : int | None
        Number of grid points in y direction.

    Returns
    -------
    lon : np.ndarray
        2D longitude grid array of shape (Ny, Nx) in degrees [-180, 180] or [0, 360].
    lat : np.ndarray
        2D latitude grid array of shape (Ny, Nx) in degrees [-90, 90].
    """
    if nx is not None:
        x1d = np.linspace(-extent_km * 1000.0, extent_km * 1000.0, nx)
    else:
        x1d = np.arange(-extent_km * 1000.0, extent_km * 1000.0 + resolution_km * 500.0, resolution_km * 1000.0)

    if ny is not None:
        y1d = np.linspace(-extent_km * 1000.0, extent_km * 1000.0, ny)
    else:
        y1d = np.arange(-extent_km * 1000.0, extent_km * 1000.0 + resolution_km * 500.0, resolution_km * 1000.0)

    x, y = np.meshgrid(x1d, y1d)
    radius_earth = 6371000.0

    rho = np.hypot(x, y)
    c = 2.0 * np.arctan2(rho, 2.0 * radius_earth)

    lat0_rad = np.radians(center_lat)
    lon0_rad = np.radians(center_lon)

    with np.errstate(divide="ignore", invalid="ignore"):
        sin_c = np.sin(c)
        cos_c = np.cos(c)

        lat_rad = np.arcsin(
            cos_c * np.sin(lat0_rad) + (y * sin_c * np.cos(lat0_rad)) / np.where(rho == 0, 1.0, rho)
        )

        lon_rad = lon0_rad + np.arctan2(
            x * sin_c,
            rho * np.cos(lat0_rad) * cos_c - y * np.sin(lat0_rad) * sin_c,
        )

    lat_rad[rho == 0] = lat0_rad
    lon_rad[rho == 0] = lon0_rad

    lon = np.degrees(lon_rad)
    lat = np.degrees(lat_rad)

    # Normalize longitudes to [0, 360)
    lon = np.mod(lon, 360.0)

    return lon, lat


def create_mercator_grid(
    lon_start: float = 140.0,
    lon_end: float = 160.0,
    lat_start: float = 10.0,
    lat_end: float = 40.0,
    nx: int = 81,
    ny: int = 81,
) -> tuple[np.ndarray, np.ndarray]:
    """Generate 2D geographic coordinates for a conformal Mercator grid.

    Parameters
    ----------
    lon_start : float
        Minimum longitude in degrees.
    lon_end : float
        Maximum longitude in degrees.
    lat_start : float
        Minimum latitude in degrees.
    lat_end : float
        Maximum latitude in degrees.
    nx : int
        Number of grid points in longitude direction.
    ny : int
        Number of grid points in latitude direction.

    Returns
    -------
    lon : np.ndarray
        2D longitude grid array of shape (Ny, Nx).
    lat : np.ndarray
        2D latitude grid array of shape (Ny, Nx).
    """
    lon1d = np.linspace(lon_start, lon_end, nx)

    y_min = np.log(np.tan(np.pi / 4.0 + np.radians(lat_start) / 2.0))
    y_max = np.log(np.tan(np.pi / 4.0 + np.radians(lat_end) / 2.0))
    y1d = np.linspace(y_min, y_max, ny)

    lat1d = np.degrees(2.0 * np.arctan(np.exp(y1d)) - np.pi / 2.0)

    lon, lat = np.meshgrid(lon1d, lat1d)
    return lon, lat


def create_rotated_pole_grid(
    lon_start: float = -20.0,
    lon_end: float = 20.0,
    lat_start: float = -20.0,
    lat_end: float = 20.0,
    pole_lon: float = 180.0,
    pole_lat: float = 60.0,
    nx: int = 81,
    ny: int = 81,
) -> tuple[np.ndarray, np.ndarray]:
    """Generate 2D geographic coordinates for a rotated pole spherical grid.

    Parameters
    ----------
    lon_start : float
        Start longitude in rotated system (degrees).
    lon_end : float
        End longitude in rotated system (degrees).
    lat_start : float
        Start latitude in rotated system (degrees).
    lat_end : float
        End latitude in rotated system (degrees).
    pole_lon : float
        Longitude of the rotated north pole in geographic coordinates.
    pole_lat : float
        Latitude of the rotated north pole in geographic coordinates.
    nx : int
        Number of grid points in longitude direction.
    ny : int
        Number of grid points in latitude direction.

    Returns
    -------
    lon : np.ndarray
        2D geographic longitude grid array of shape (Ny, Nx) in range [0, 360).
    lat : np.ndarray
        2D geographic latitude grid array of shape (Ny, Nx) in range [-90, 90].
    """
    rlon1d = np.linspace(lon_start, lon_end, nx)
    rlat1d = np.linspace(lat_start, lat_end, ny)
    rlon, rlat = np.meshgrid(rlon1d, rlat1d)

    rlon_rad = np.radians(rlon)
    rlat_rad = np.radians(rlat)
    p_lon_rad = np.radians(pole_lon)
    p_lat_rad = np.radians(pole_lat)

    sin_plat = np.sin(p_lat_rad)
    cos_plat = np.cos(p_lat_rad)

    sin_rlat = np.sin(rlat_rad)
    cos_rlat = np.cos(rlat_rad)
    sin_rlon = np.sin(rlon_rad)
    cos_rlon = np.cos(rlon_rad)

    lat_rad = np.arcsin(sin_plat * sin_rlat + cos_plat * cos_rlat * cos_rlon)
    lon_rad = p_lon_rad + np.arctan2(
        cos_rlat * sin_rlon,
        cos_plat * sin_rlat - sin_plat * cos_rlat * cos_rlon,
    )

    lon = np.degrees(lon_rad)
    lat = np.degrees(lat_rad)

    lon = np.mod(lon, 360.0)
    return lon, lat


def create_grid_coordinates(
    grid_type: str = "regular",
    **kwargs,
) -> tuple[np.ndarray, np.ndarray]:
    """Unified entry point to create 2D grid coordinates for WW3 / WW4.

    Parameters
    ----------
    grid_type : str
        Grid projection or layout type. Supported options:
        - 'regular', 'latlon', 'rectilinear': Regular 2D lon-lat grid.
        - 'polar_stereographic', 'stereographic': Polar stereographic grid.
        - 'mercator': Mercator projection grid.
        - 'rotated_pole', 'curvilinear': Rotated pole spherical grid.
    **kwargs
        Parameters passed to the specific grid generator.

    Returns
    -------
    lon : np.ndarray
        2D longitude array of shape (Ny, Nx).
    lat : np.ndarray
        2D latitude array of shape (Ny, Nx).
    """
    gtype = grid_type.lower().strip()
    if gtype in ("regular", "latlon", "rectilinear"):
        return create_regular_grid(**kwargs)
    elif gtype in ("polar_stereographic", "stereographic"):
        return create_polar_stereographic_grid(**kwargs)
    elif gtype == "mercator":
        return create_mercator_grid(**kwargs)
    elif gtype in ("rotated_pole", "curvilinear"):
        return create_rotated_pole_grid(**kwargs)
    else:
        raise ValueError(
            f"Unsupported grid_type '{grid_type}'. Supported grid types: "
            "'regular', 'polar_stereographic', 'mercator', 'rotated_pole'."
        )
