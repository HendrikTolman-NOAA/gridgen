# WAVEWATCH III (WW3) / WAVEWATCH IV (WW4) Gridgen Package
#
# Copyright 2026 National Weather Service (NWS), NOAA. All rights reserved.
# NWS often uses Generative AI (GenAI) for code development and refactoring.
# Whenever GenAI is used, NWS requires a full human review of code before it
# is added to its repositories.
#
# @file coordinates.py
# @brief Grid coordinate generation module for WAVEWATCH III / WAVEWATCH IV.
# @author Aldgisl (Agentic AI), Hendrik Tolman
# @author Jules (Agentic AI) (contributor)
# @date Initial: 2026-10-06
# @date Latest Update: 2026-11-05

"""Grid coordinate generation module for WAVEWATCH III (WW3) / WAVEWATCH IV (WW4).

Provides 2D coordinate generation routines for regular, general stereographic,
rotated pole grid geometries, and custom grid layout files.
"""

from __future__ import annotations

import inspect
from pathlib import Path

import numpy as np


def geo_to_rotated_coords(
    lon: float | np.ndarray,
    lat: float | np.ndarray,
    pole_lon: float,
    pole_lat: float,
) -> tuple[float | np.ndarray, float | np.ndarray]:
    """Convert traditional geographic coordinates (lon, lat) to rotated-pole coordinates.

    Parameters
    ----------
    lon : float or np.ndarray
        Geographic longitude in degrees.
    lat : float or np.ndarray
        Geographic latitude in degrees.
    pole_lon : float
        Geographic longitude of the rotated North Pole in degrees.
    pole_lat : float
        Geographic latitude of the rotated North Pole in degrees.

    Returns
    -------
    rlon : float or np.ndarray
        Rotated-pole longitude in degrees [-180, 180].
    rlat : float or np.ndarray
        Rotated-pole latitude in degrees [-90, 90].
    """
    is_scalar = np.isscalar(lon) and np.isscalar(lat)
    lon_arr = np.asarray(lon, dtype=np.float64)
    lat_arr = np.asarray(lat, dtype=np.float64)

    lon_rad = np.radians(lon_arr)
    lat_rad = np.radians(lat_arr)
    p_lon_rad = np.radians(pole_lon)
    p_lat_rad = np.radians(pole_lat)

    sin_plat = np.sin(p_lat_rad)
    cos_plat = np.cos(p_lat_rad)
    sin_lat = np.sin(lat_rad)
    cos_lat = np.cos(lat_rad)
    dlon_rad = lon_rad - p_lon_rad
    sin_dlon = np.sin(dlon_rad)
    cos_dlon = np.cos(dlon_rad)

    z_rot = sin_plat * sin_lat + cos_plat * cos_lat * cos_dlon
    x_rot = cos_plat * sin_lat - sin_plat * cos_lat * cos_dlon
    y_rot = cos_lat * sin_dlon

    rlat_rad = np.arcsin(np.clip(z_rot, -1.0, 1.0))
    rlon_rad = np.arctan2(y_rot, x_rot)

    rlon_out = np.degrees(rlon_rad)
    rlat_out = np.degrees(rlat_rad)

    if is_scalar:
        return float(rlon_out), float(rlat_out)
    return rlon_out, rlat_out


def rotated_to_geo_coords(
    rlon: float | np.ndarray,
    rlat: float | np.ndarray,
    pole_lon: float,
    pole_lat: float,
) -> tuple[float | np.ndarray, float | np.ndarray]:
    """Convert rotated-pole coordinates (rlon, rlat) to traditional geographic coordinates.

    Parameters
    ----------
    rlon : float or np.ndarray
        Rotated-pole longitude in degrees.
    rlat : float or np.ndarray
        Rotated-pole latitude in degrees.
    pole_lon : float
        Geographic longitude of the rotated North Pole in degrees.
    pole_lat : float
        Geographic latitude of the rotated North Pole in degrees.

    Returns
    -------
    lon : float or np.ndarray
        Geographic longitude in degrees [0, 360).
    lat : float or np.ndarray
        Geographic latitude in degrees [-90, 90].
    """
    is_scalar = np.isscalar(rlon) and np.isscalar(rlat)
    rlon_arr = np.asarray(rlon, dtype=np.float64)
    rlat_arr = np.asarray(rlat, dtype=np.float64)

    rlon_rad = np.radians(rlon_arr)
    rlat_rad = np.radians(rlat_arr)
    p_lon_rad = np.radians(pole_lon)
    p_lat_rad = np.radians(pole_lat)

    sin_plat = np.sin(p_lat_rad)
    cos_plat = np.cos(p_lat_rad)
    sin_rlat = np.sin(rlat_rad)
    cos_rlat = np.cos(rlat_rad)
    sin_rlon = np.sin(rlon_rad)
    cos_rlon = np.cos(rlon_rad)

    lat_rad = np.arcsin(
        np.clip(sin_plat * sin_rlat + cos_plat * cos_rlat * cos_rlon, -1.0, 1.0)
    )
    lon_rad = p_lon_rad + np.arctan2(
        cos_rlat * sin_rlon,
        cos_plat * sin_rlat - sin_plat * cos_rlat * cos_rlon,
    )

    lon_out = np.mod(np.degrees(lon_rad), 360.0)
    lat_out = np.degrees(lat_rad)

    if is_scalar:
        return float(lon_out), float(lat_out)
    return lon_out, lat_out


def create_regular_grid(
    LON_START: float | None = 0.0,
    LAT_START: float | None = -90.0,
    LON_END: float | None = None,
    LAT_END: float | None = None,
    NX: int = 1440,
    NY: int = 601,
    POLE_LON: float | None = 0.0,
    POLE_LAT: float | None = 90.0,
    SX: float | None = None,
    SY: float | None = None,
    DX: float | None = None,
    DY: float | None = None,
    DLON: float | None = None,
    DLAT: float | None = None,
    GLOBAL_CLOSURE: bool = False,
    global_closure: bool = False,
) -> tuple[np.ndarray, np.ndarray]:
    """Generate 2D arrays of longitude and latitude for a regular grid.

    Requires lower-left corner bounding points (LON_START, LAT_START) as mandatory parameters.
    Requires either upper-right corner coordinates (LON_END, LAT_END) OR grid increments
    (SX/DX/DLON, SY/DY/DLAT). Accepts discrete matrix dimensions (NX, NY). Optionally accepts
    rotated pole coordinates (POLE_LON, POLE_LAT). If POLE_LAT is None or 90.0, the grid
    reverts to standard unrotated regular geographic coordinates.

    Parameters
    ----------
    LON_START : float | None
        [Mandatory] Lower-left corner longitude in degrees.
    LAT_START : float | None
        [Mandatory] Lower-left corner latitude in degrees.
    LON_END : float | None
        [Mandatory if SX/DX/DLON omitted] Upper-right corner longitude in degrees.
    LAT_END : float | None
        [Mandatory if SY/DY/DLAT omitted] Upper-right corner latitude in degrees.
    NX : int
        Number of grid points in longitude / X direction (default: 1440).
    NY : int
        Number of grid points in latitude / Y direction (default: 601).
    POLE_LON : float | None
        Longitude of rotated north pole in geographic coordinates (optional).
    POLE_LAT : float | None
        Latitude of rotated north pole in geographic coordinates (optional, default: 90.0).
    SX / DX / DLON : float | None
        [Mandatory if LON_END omitted] Longitude grid increment in degrees.
    SY / DY / DLAT : float | None
        [Mandatory if LAT_END omitted] Latitude grid increment in degrees.

    Returns
    -------
    lon : np.ndarray
        2D longitude grid array of shape (NY, NX).
    lat : np.ndarray
        2D latitude grid array of shape (NY, NX).
    """
    lon_start_val = 0.0 if LON_START is None else float(LON_START)
    lat_start_val = -90.0 if LAT_START is None else float(LAT_START)

    sx_given = SX if SX is not None else (DX if DX is not None else DLON)
    is_global = GLOBAL_CLOSURE or global_closure
    if sx_given is not None and np.isclose(float(NX) * float(sx_given), 360.0):
        is_global = True

    if is_global:
        sx_val = 360.0 / float(NX)
        lon_end_val = lon_start_val + (NX - 1) * sx_val
    else:
        sx_val = sx_given
        if LON_END is None and sx_val is None:
            lon_end_val = 359.75 if (lon_start_val == 0.0 and NX == 1440) else lon_start_val + (NX - 1) * 0.25
        elif LON_END is not None:
            lon_end_val = float(LON_END)
        else:
            lon_end_val = lon_start_val + (NX - 1) * sx_val

    sy_val = SY if SY is not None else (DY if DY is not None else DLAT)

    if LAT_END is None and sy_val is None:
        lat_end_val = 90.0 if (lat_start_val == -90.0 and NY == 601) else lat_start_val + (NY - 1) * 0.3
    elif LAT_END is not None:
        lat_end_val = float(LAT_END)
    else:
        lat_end_val = lat_start_val + (NY - 1) * sy_val

    if POLE_LAT is None or POLE_LAT == 90.0:
        lon1d = np.linspace(lon_start_val, lon_end_val, NX)
        lat1d = np.linspace(lat_start_val, lat_end_val, NY)
        lon, lat = np.meshgrid(lon1d, lat1d)
        return lon, lat

    pole_lon = 0.0 if POLE_LON is None else float(POLE_LON)
    pole_lat = float(POLE_LAT)

    # 1) Determine the center point of the grid in traditional lon-lat space
    center_lon = 0.5 * (lon_start_val + lon_end_val)
    center_lat = 0.5 * (lat_start_val + lat_end_val)

    # 2) Determine coordinates of this point in rotated-pole lon-lat coordinates
    c_rlon, c_rlat = geo_to_rotated_coords(center_lon, center_lat, pole_lon, pole_lat)

    # 3) Determine SX and SY in rotated coordinates and create rotated grid centered on (c_rlon, c_rlat)
    sx_rot = (
        sx_val
        if sx_val is not None
        else ((lon_end_val - lon_start_val) / (NX - 1) if NX > 1 else 0.0)
    )
    sy_rot = (
        sy_val
        if sy_val is not None
        else ((lat_end_val - lat_start_val) / (NY - 1) if NY > 1 else 0.0)
    )

    rlon_start = c_rlon - 0.5 * (NX - 1) * sx_rot
    rlon_end = c_rlon + 0.5 * (NX - 1) * sx_rot
    rlat_start = c_rlat - 0.5 * (NY - 1) * sy_rot
    rlat_end = c_rlat + 0.5 * (NY - 1) * sy_rot

    rlon1d = np.linspace(rlon_start, rlon_end, NX)
    rlat1d = np.linspace(rlat_start, rlat_end, NY)
    rlon_grid, rlat_grid = np.meshgrid(rlon1d, rlat1d)

    # 4) Map each of the grid points in the resulting grid back to traditional lon-lat coordinates
    lon, lat = rotated_to_geo_coords(rlon_grid, rlat_grid, pole_lon, pole_lat)
    return lon, lat


def create_stereographic_grid(
    CENTER_LON: float = 0.0,
    CENTER_LAT: float = 90.0,
    EXTENT_DEG: float | None = None,
    NX: int | None = 1440,
    NY: int | None = 601,
    ROTATION: float = 0.0,
    k0: float = 1.0,
) -> tuple[np.ndarray, np.ndarray]:
    """Generate 2D geographic coordinates for a general stereographic grid.

    Domain size is defined by EXTENT_DEG, which specifies the distance from the
    center of the grid to the edge of the grid in arc degrees along the smaller of
    the discrete dimensions NX and NY, with optional planar rotation angle ROTATION in degrees.

    Parameters
    ----------
    CENTER_LON : float
        Central meridian of projection in degrees (default: 0.0).
    CENTER_LAT : float
        Central latitude of projection in degrees (-90 to +90, default: 90.0).
    EXTENT_DEG : float
        [Mandatory] Half-width extent of domain in arc degrees from center to edge.
    NX : int | None
        Number of grid points in x direction (default: 1440).
    NY : int | None
        Number of grid points in y direction (default: 601).
    ROTATION : float
        Optional grid rotation angle in degrees on projection plane (default: 0.0).
    k0 : float
        Scale factor at projection origin (default: 1.0).

    Returns
    -------
    lon : np.ndarray
        2D longitude grid array of shape (NY, NX) in degrees [0, 360).
    lat : np.ndarray
        2D latitude grid array of shape (NY, NX) in degrees [-90, 90].
    """
    if EXTENT_DEG is None:
        raise ValueError(
            "EXTENT_DEG is mandatory for stereographic grid."
        )

    radius_earth = 6371000.0  # meters

    nx_val = NX if NX is not None else 1440
    ny_val = NY if NY is not None else 601

    if nx_val <= 1 or ny_val <= 1:
        raise ValueError(
            f"NX and NY must be greater than 1, got NX={nx_val}, NY={ny_val}"
        )

    # Physical radial distance from center to edge on stereographic projection plane
    c_extent = np.radians(float(EXTENT_DEG))
    rho_extent = 2.0 * k0 * radius_earth * np.tan(c_extent / 2.0)

    # Apply the extent to the smaller of NX and NY to determine grid spacing d
    n_min = min(nx_val, ny_val)
    d = (2.0 * rho_extent) / (n_min - 1)

    half_x = 0.5 * (nx_val - 1) * d
    half_y = 0.5 * (ny_val - 1) * d

    x1d = np.linspace(-half_x, half_x, nx_val)
    y1d = np.linspace(-half_y, half_y, ny_val)

    x, y = np.meshgrid(x1d, y1d)

    if ROTATION != 0.0:
        rot_rad = np.radians(ROTATION)
        cos_r = np.cos(rot_rad)
        sin_r = np.sin(rot_rad)
        xr = x * cos_r - y * sin_r
        yr = x * sin_r + y * cos_r
    else:
        xr = x
        yr = y

    rho = np.hypot(xr, yr)
    c = 2.0 * np.arctan2(rho, 2.0 * k0 * radius_earth)

    lat0_rad = np.radians(CENTER_LAT)
    lon0_rad = np.radians(CENTER_LON)

    sin_lat0 = np.sin(lat0_rad)
    cos_lat0 = np.cos(lat0_rad)

    with np.errstate(divide="ignore", invalid="ignore"):
        sin_c = np.sin(c)
        cos_c = np.cos(c)

        rho_safe = np.where(rho == 0, 1.0, rho)

        lat_rad = np.arcsin(cos_c * sin_lat0 + (yr * sin_c * cos_lat0) / rho_safe)

        lon_rad = lon0_rad + np.arctan2(
            xr * sin_c,
            rho_safe * cos_lat0 * cos_c - yr * sin_lat0 * sin_c,
        )

    lat_rad[rho == 0] = lat0_rad
    lon_rad[rho == 0] = lon0_rad

    lon = np.degrees(lon_rad)
    lat = np.degrees(lat_rad)

    lon = np.mod(lon, 360.0)
    return lon, lat


def create_rotated_pole_grid(
    POLE_LON: float,
    POLE_LAT: float,
    LON_START: float = -20.0,
    LON_END: float = 20.0,
    LAT_START: float = -20.0,
    LAT_END: float = 20.0,
    NX: int = 81,
    NY: int = 81,
) -> tuple[np.ndarray, np.ndarray]:
    """Generate 2D geographic coordinates for a rotated pole spherical grid.

    Parameters
    ----------
    POLE_LON : float
        Longitude of the rotated north pole in geographic coordinates.
    POLE_LAT : float
        Latitude of the rotated north pole in geographic coordinates.
    LON_START : float
        Start longitude in rotated system (degrees).
    LON_END : float
        End longitude in rotated system (degrees).
    LAT_START : float
        Start latitude in rotated system (degrees).
    LAT_END : float
        End latitude in rotated system (degrees).
    NX : int
        Number of grid points in longitude direction.
    NY : int
        Number of grid points in latitude direction.

    Returns
    -------
    lon : np.ndarray
        2D geographic longitude grid array of shape (NY, NX) in range [0, 360).
    lat : np.ndarray
        2D geographic latitude grid array of shape (NY, NX) in range [-90, 90].
    """
    rlon1d = np.linspace(LON_START, LON_END, NX)
    rlat1d = np.linspace(LAT_START, LAT_END, NY)
    rlon, rlat = np.meshgrid(rlon1d, rlat1d)

    rlon_rad = np.radians(rlon)
    rlat_rad = np.radians(rlat)
    p_lon_rad = np.radians(POLE_LON)
    p_lat_rad = np.radians(POLE_LAT)

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
        2D longitude array of shape (NY, NX).
    lat : np.ndarray
        2D latitude array of shape (NY, NX).
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
            for key in ds.variables:
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
        lon_key = next(
            (k for k in data.files if k.lower() in ("lon", "longitude", "x")), None
        )
        lat_key = next(
            (k for k in data.files if k.lower() in ("lat", "latitude", "y")), None
        )
        if not lon_key or not lat_key:
            raise ValueError(
                f"Could not find 'lon' and 'lat' keys in NPZ file '{filepath}'. Keys: {data.files}"
            )
        lon_arr = np.array(data[lon_key])
        lat_arr = np.array(data[lat_key])

    elif ext == ".npy":
        arr = np.load(path, allow_pickle=True)
        if (
            isinstance(arr, np.ndarray)
            and arr.dtype.names
            and ("lon" in arr.dtype.names)
            and ("lat" in arr.dtype.names)
        ):
            lon_arr = arr["lon"]
            lat_arr = arr["lat"]
        elif isinstance(arr, tuple) or (
            isinstance(arr, np.ndarray) and arr.ndim == 3 and arr.shape[0] == 2
        ):
            lon_arr, lat_arr = arr[0], arr[1]
        else:
            raise ValueError(
                f"Unable to parse 2D lon and lat from NPY file '{filepath}'."
            )

    elif ext == ".mat":
        from scipy.io import loadmat

        mat = loadmat(path)
        lon_key = next((k for k in mat if k.lower() in ("lon", "longitude", "x")), None)
        lat_key = next((k for k in mat if k.lower() in ("lat", "latitude", "y")), None)
        if not lon_key or not lat_key:
            raise ValueError(
                f"Could not find 'lon' and 'lat' variables in MAT file '{filepath}'. Keys: {list(mat.keys())}"
            )
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
            raise ValueError(
                f"ASCII grid file '{filepath}' must contain 2 columns or 2 rows for lon and lat."
            )
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
    res = {}
    for k, v in kwargs.items():
        if v is not None:
            if k in valid_params:
                res[k] = v
            elif k.upper() in valid_params:
                res[k.upper()] = v
            elif k.lower() in valid_params:
                res[k.lower()] = v
    return res


def validate_grid_parameters(grid_type: str, kwargs: dict) -> None:
    """Validate mandatory input parameters for the requested grid type.

    Parameters
    ----------
    grid_type : str
        Normalized grid type identifier.
    kwargs : dict
        Keyword arguments supplied for grid creation.

    Raises
    ------
    ValueError
        If required parameters for the specified grid type are missing or invalid.
    """
    gtype = grid_type.lower().strip()

    if gtype == "custom":
        custom_file = kwargs.get("custom_grid") or kwargs.get("filepath")
        if not custom_file:
            raise ValueError(
                "Missing mandatory parameter '--custom-grid' for custom grid type."
            )
        return

    # Check discrete dimensions NX and NY if provided or required
    nx = kwargs.get("NX") if kwargs.get("NX") is not None else kwargs.get("nx")
    ny = kwargs.get("NY") if kwargs.get("NY") is not None else kwargs.get("ny")
    if nx is not None and int(nx) <= 0:
        raise ValueError(f"Grid dimension NX must be positive, got {nx}")
    if ny is not None and int(ny) <= 0:
        raise ValueError(f"Grid dimension NY must be positive, got {ny}")

    if gtype == "stereographic":
        extent_deg = kwargs.get("EXTENT_DEG") if kwargs.get("EXTENT_DEG") is not None else kwargs.get("extent_deg")
        if extent_deg is None:
            raise ValueError(
                "Missing mandatory parameter '--extent-deg' (EXTENT_DEG) for stereographic grid."
            )
        return
    elif gtype == "regular":
        return
    else:
        raise ValueError(
            f"Unsupported grid_type '{grid_type}'. Supported grid types: "
            "'regular', 'stereographic', 'custom'."
        )


def create_grid_coordinates(
    grid_type: str = "regular",
    **kwargs,
) -> tuple[np.ndarray, np.ndarray]:
    """Unified entry point to create 2D grid coordinates for WW3 / WW4.

    Parameters
    ----------
    grid_type : str
        Grid projection or layout type. Supported options:
        - 'regular': Regular 2D lon-lat grid (with optional rotated pole via POLE_LON, POLE_LAT).
        - 'stereographic': General stereographic grid (via EXTENT_DEG).
        - 'custom': Custom grid loaded from a layout file specified via custom_grid/filepath parameter.
    **kwargs
        Parameters passed to the specific grid generator or custom_grid filepath.

    Returns
    -------
    lon : np.ndarray
        2D longitude array of shape (NY, NX).
    lat : np.ndarray
        2D latitude array of shape (NY, NX).
    """
    gtype = grid_type.lower().strip()

    validate_grid_parameters(gtype, kwargs)

    custom_file = kwargs.get("custom_grid") or kwargs.get("filepath")
    if gtype == "custom" or custom_file is not None:
        if not custom_file:
            raise ValueError(
                "Parameter 'custom_grid' (filepath) must be provided when grid_type is 'custom'."
            )
        return load_custom_grid(custom_file)

    if gtype == "regular":
        filtered = _filter_kwargs(create_regular_grid, kwargs)
        return create_regular_grid(**filtered)
    elif gtype == "stereographic":
        filtered = _filter_kwargs(create_stereographic_grid, kwargs)
        return create_stereographic_grid(**filtered)
    else:
        raise ValueError(
            f"Unsupported grid_type '{grid_type}'. Supported grid types: "
            "'regular', 'stereographic', 'custom'."
        )
