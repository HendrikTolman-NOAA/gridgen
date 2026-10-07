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
# @date Latest Update: 2026-10-07

"""Grid coordinate generation module for WAVEWATCH III (WW3) / WAVEWATCH IV (WW4).

Provides 2D coordinate generation routines for regular, general stereographic,
Lambert Conformal Conic, rotated pole grid geometries, and custom grid layout files.
"""

from __future__ import annotations

import inspect
from pathlib import Path

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


def create_stereographic_grid(
    center_lon: float = 0.0,
    center_lat: float = 90.0,
    extent_km: float = 2000.0,
    resolution_km: float = 50.0,
    nx: int | None = None,
    ny: int | None = None,
    k0: float = 1.0,
) -> tuple[np.ndarray, np.ndarray]:
    """Generate 2D geographic coordinates for a general stereographic grid.

    Supports polar, oblique, and equatorial stereographic projections.

    Parameters
    ----------
    center_lon : float
        Central meridian of projection in degrees.
    center_lat : float
        Central latitude of projection in degrees (-90 to +90).
    extent_km : float
        Half-width extent of domain in kilometers.
    resolution_km : float
        Grid spacing in kilometers.
    nx : int | None
        Number of grid points in x direction.
    ny : int | None
        Number of grid points in y direction.
    k0 : float
        Scale factor at projection origin (default: 1.0).

    Returns
    -------
    lon : np.ndarray
        2D longitude grid array of shape (Ny, Nx) in degrees [0, 360).
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
    c = 2.0 * np.arctan2(rho, 2.0 * k0 * radius_earth)

    lat0_rad = np.radians(center_lat)
    lon0_rad = np.radians(center_lon)

    sin_lat0 = np.sin(lat0_rad)
    cos_lat0 = np.cos(lat0_rad)

    with np.errstate(divide="ignore", invalid="ignore"):
        sin_c = np.sin(c)
        cos_c = np.cos(c)

        rho_safe = np.where(rho == 0, 1.0, rho)

        lat_rad = np.arcsin(
            cos_c * sin_lat0 + (y * sin_c * cos_lat0) / rho_safe
        )

        lon_rad = lon0_rad + np.arctan2(
            x * sin_c,
            rho_safe * cos_lat0 * cos_c - y * sin_lat0 * sin_c,
        )

    lat_rad[rho == 0] = lat0_rad
    lon_rad[rho == 0] = lon0_rad

    lon = np.degrees(lon_rad)
    lat = np.degrees(lat_rad)

    lon = np.mod(lon, 360.0)
    return lon, lat


def create_lambert_conformal_grid(
    center_lon: float = 0.0,
    center_lat: float = 40.0,
    lat_1: float = 30.0,
    lat_2: float = 60.0,
    extent_km: float = 2000.0,
    resolution_km: float = 50.0,
    nx: int | None = None,
    ny: int | None = None,
) -> tuple[np.ndarray, np.ndarray]:
    """Generate 2D geographic coordinates for a Lambert Conformal Conic grid.

    Parameters
    ----------
    center_lon : float
        Central meridian of projection in degrees.
    center_lat : float
        Central latitude of projection in degrees.
    lat_1 : float
        First standard parallel in degrees.
    lat_2 : float
        Second standard parallel in degrees.
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
        2D longitude grid array of shape (Ny, Nx) in degrees [0, 360).
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

    phi_0 = np.radians(center_lat)
    phi_1 = np.radians(lat_1)
    phi_2 = np.radians(lat_2)
    lam_0 = np.radians(center_lon)

    if abs(phi_1 - phi_2) < 1e-8:
        n = np.sin(phi_1)
    else:
        n = np.log(np.cos(phi_1) / np.cos(phi_2)) / np.log(
            np.tan(np.pi / 4.0 + phi_2 / 2.0) / np.tan(np.pi / 4.0 + phi_1 / 2.0)
        )

    F = (np.cos(phi_1) * (np.tan(np.pi / 4.0 + phi_1 / 2.0) ** n)) / n
    r_0 = radius_earth * F / (np.tan(np.pi / 4.0 + phi_0 / 2.0) ** n)

    sign_n = np.sign(n) if n != 0 else 1.0

    r = sign_n * np.hypot(x, r_0 - y)
    theta = np.arctan2(sign_n * x, sign_n * (r_0 - y))

    lon_rad = lam_0 + theta / n
    with np.errstate(divide="ignore", invalid="ignore"):
        lat_rad = 2.0 * np.arctan((radius_earth * F / r) ** (1.0 / n)) - np.pi / 2.0

    lon = np.degrees(lon_rad)
    lat = np.degrees(lat_rad)

    lon = np.mod(lon, 360.0)
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


def load_custom_grid(filepath: str | Path) -> tuple[np.ndarray, np.ndarray]:
    """Load 2D longitude and latitude coordinate arrays from a custom grid layout file.

    Supports NetCDF (.nc), NumPy archive (.npz, .npy), MATLAB (.mat), and ASCII (.dat, .txt, .csv) files.

    Parameters
    ----------
    filepath : str | Path
        Path to the custom grid layout file.

    Returns
    -------
    lon : np.ndarray
        2D longitude array of shape (Ny, Nx).
    lat : np.ndarray
        2D latitude array of shape (Ny, Nx).
    """
    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"Custom grid file not found: '{filepath}'")

    ext = path.suffix.lower()

    if ext in (".nc", ".nc4", ".cdf"):
        import netCDF4 as nc

        with nc.Dataset(path, "r") as ds:
            lon_var = None
            lat_var = None
            for key in ds.variables.keys():
                k_lower = key.lower()
                if k_lower in ("lon", "longitude", "grid_lon", "x", "nav_lon", "lons"):
                    lon_var = key
                elif k_lower in ("lat", "latitude", "grid_lat", "y", "nav_lat", "lats"):
                    lat_var = key

            if not lon_var or not lat_var:
                raise ValueError(
                    f"Could not identify longitude and latitude variables in NetCDF file '{filepath}'. "
                    f"Available variables: {list(ds.variables.keys())}"
                )

            lon_arr = np.array(ds.variables[lon_var][:])
            lat_arr = np.array(ds.variables[lat_var][:])

    elif ext == ".npz":
        data = np.load(path)
        lon_key = next((k for k in data.files if k.lower() in ("lon", "longitude", "x")), None)
        lat_key = next((k for k in data.files if k.lower() in ("lat", "latitude", "y")), None)
        if not lon_key or not lat_key:
            raise ValueError(f"Could not find 'lon' and 'lat' keys in NPZ file '{filepath}'. Keys: {data.files}")
        lon_arr = np.array(data[lon_key])
        lat_arr = np.array(data[lat_key])

    elif ext == ".npy":
        arr = np.load(path, allow_pickle=True)
        if isinstance(arr, np.ndarray) and arr.dtype.names and ("lon" in arr.dtype.names) and ("lat" in arr.dtype.names):
            lon_arr = arr["lon"]
            lat_arr = arr["lat"]
        elif isinstance(arr, tuple) or (isinstance(arr, np.ndarray) and arr.ndim == 3 and arr.shape[0] == 2):
            lon_arr, lat_arr = arr[0], arr[1]
        else:
            raise ValueError(f"Unable to parse 2D lon and lat from NPY file '{filepath}'.")

    elif ext == ".mat":
        from scipy.io import loadmat

        mat = loadmat(path)
        lon_key = next((k for k in mat.keys() if k.lower() in ("lon", "longitude", "x")), None)
        lat_key = next((k for k in mat.keys() if k.lower() in ("lat", "latitude", "y")), None)
        if not lon_key or not lat_key:
            raise ValueError(f"Could not find 'lon' and 'lat' variables in MAT file '{filepath}'. Keys: {list(mat.keys())}")
        lon_arr = np.array(mat[lon_key])
        lat_arr = np.array(mat[lat_key])

    elif ext in (".dat", ".txt", ".csv"):
        delimiter = "," if ext == ".csv" else None
        data = np.loadtxt(path, delimiter=delimiter)
        if data.ndim == 2 and data.shape[1] == 2:
            lon_arr = data[:, 0]
            lat_arr = data[:, 1]
        elif data.ndim == 2 and data.shape[0] == 2:
            lon_arr = data[0, :]
            lat_arr = data[1, :]
        else:
            raise ValueError(f"ASCII grid file '{filepath}' must contain 2 columns or 2 rows for lon and lat.")
    else:
        raise ValueError(
            f"Unsupported custom grid file format '{ext}'. "
            "Supported formats: .nc, .npz, .npy, .mat, .dat, .txt, .csv"
        )

    lon_arr = np.squeeze(lon_arr)
    lat_arr = np.squeeze(lat_arr)

    if lon_arr.ndim == 1 and lat_arr.ndim == 1:
        lon_arr, lat_arr = np.meshgrid(lon_arr, lat_arr)
    elif lon_arr.ndim != 2 or lat_arr.ndim != 2:
        raise ValueError(
            f"Coordinates in '{filepath}' must be 1D or 2D. "
            f"Got shapes lon: {lon_arr.shape}, lat: {lat_arr.shape}"
        )

    if lon_arr.shape != lat_arr.shape:
        raise ValueError(
            f"Longitude shape {lon_arr.shape} does not match latitude shape {lat_arr.shape} in '{filepath}'."
        )

    return lon_arr, lat_arr


def _filter_kwargs(func, kwargs: dict) -> dict:
    """Helper to extract valid keyword arguments for a target function."""
    sig = inspect.signature(func)
    valid_params = set(sig.parameters.keys())
    return {k: v for k, v in kwargs.items() if k in valid_params and v is not None}


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
        - 'stereographic', 'polar_stereographic': General stereographic grid.
        - 'lambert_conformal', 'lambert': Lambert Conformal Conic grid.
        - 'rotated_pole', 'curvilinear': Rotated pole spherical grid.
        - 'custom': Custom grid loaded from a layout file specified via custom_grid/filepath parameter.
    **kwargs
        Parameters passed to the specific grid generator or custom_grid filepath.

    Returns
    -------
    lon : np.ndarray
        2D longitude array of shape (Ny, Nx).
    lat : np.ndarray
        2D latitude array of shape (Ny, Nx).
    """
    gtype = grid_type.lower().strip()
    custom_file = kwargs.get("custom_grid") or kwargs.get("filepath")
    if gtype == "custom" or custom_file is not None:
        if not custom_file:
            raise ValueError("Parameter 'custom_grid' (filepath) must be provided when grid_type is 'custom'.")
        return load_custom_grid(custom_file)

    if gtype in ("regular", "latlon", "rectilinear"):
        filtered = _filter_kwargs(create_regular_grid, kwargs)
        return create_regular_grid(**filtered)
    elif gtype in ("stereographic", "polar_stereographic"):
        filtered = _filter_kwargs(create_stereographic_grid, kwargs)
        return create_stereographic_grid(**filtered)
    elif gtype in ("lambert_conformal", "lambert"):
        filtered = _filter_kwargs(create_lambert_conformal_grid, kwargs)
        return create_lambert_conformal_grid(**filtered)
    elif gtype in ("rotated_pole", "curvilinear"):
        filtered = _filter_kwargs(create_rotated_pole_grid, kwargs)
        return create_rotated_pole_grid(**filtered)
    else:
        raise ValueError(
            f"Unsupported grid_type '{grid_type}'. Supported grid types: "
            "'regular', 'stereographic', 'lambert_conformal', 'rotated_pole', 'custom'."
        )
