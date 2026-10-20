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
# @date Latest Update: 2026-10-19

"""Grid coordinate generation module for WAVEWATCH III (WW3) / WAVEWATCH IV (WW4).

Provides 2D coordinate generation routines for regular, general stereographic,
rotated pole grid geometries, and custom grid layout files.
"""

from __future__ import annotations

import inspect
from pathlib import Path

import numpy as np


def create_regular_grid(
    LON_START: float | None = None,
    LAT_START: float | None = None,
    LON_END: float | None = None,
    LAT_END: float | None = None,
    NX: int = 1440,
    NY: int = 601,
    POLE_LON: float | None = None,
    POLE_LAT: float | None = None,
    SX: float | None = None,
    SY: float | None = None,
    DX: float | None = None,
    DY: float | None = None,
    DLON: float | None = None,
    DLAT: float | None = None,
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
    if LON_START is None or LAT_START is None:
        missing = []
        if LON_START is None:
            missing.append("LON_START (lower longitude)")
        if LAT_START is None:
            missing.append("LAT_START (lower latitude)")
        raise ValueError(
            f"Mandatory parameter missing for regular grid: {', '.join(missing)}"
        )

    sx_val = SX if SX is not None else (DX if DX is not None else DLON)
    sy_val = SY if SY is not None else (DY if DY is not None else DLAT)

    if LON_END is None and sx_val is None:
        raise ValueError(
            "Mandatory parameter missing for regular grid: must provide either "
            "last longitude (LON_END) or longitude grid increment (SX)."
        )

    if LAT_END is None and sy_val is None:
        raise ValueError(
            "Mandatory parameter missing for regular grid: must provide either "
            "last latitude (LAT_END) or latitude grid increment (SY)."
        )

    lon_end_val = LON_END if LON_END is not None else LON_START + (NX - 1) * sx_val
    lat_end_val = LAT_END if LAT_END is not None else LAT_START + (NY - 1) * sy_val

    if POLE_LAT is None or POLE_LAT == 90.0:
        lon1d = np.linspace(LON_START, lon_end_val, NX)
        lat1d = np.linspace(LAT_START, lat_end_val, NY)
        lon, lat = np.meshgrid(lon1d, lat1d)
        return lon, lat

    pole_lon = 0.0 if POLE_LON is None else POLE_LON
    return create_rotated_pole_grid(
        POLE_LON=pole_lon,
        POLE_LAT=POLE_LAT,
        LON_START=LON_START,
        LON_END=lon_end_val,
        LAT_START=LAT_START,
        LAT_END=lat_end_val,
        NX=NX,
        NY=NY,
    )


def create_stereographic_grid(
    CENTER_LON: float,
    CENTER_LAT: float,
    EXTENT_KM: float | None = None,
    EXTENT_DEG: float | None = None,
    NX: int | None = 1440,
    NY: int | None = 601,
    ROTATION: float = 0.0,
    k0: float = 1.0,
) -> tuple[np.ndarray, np.ndarray]:
    """Generate 2D geographic coordinates for a general stereographic grid.

    Supports domain size definition either in kilometers (EXTENT_KM)
    or in arc degrees (EXTENT_DEG) over discrete dimensions (NX, NY) with optional
    planar rotation angle ROTATION in degrees.

    Parameters
    ----------
    CENTER_LON : float
        Central meridian of projection in degrees.
    CENTER_LAT : float
        Central latitude of projection in degrees (-90 to +90).
    EXTENT_KM : float | None
        Half-width extent of domain in kilometers.
    EXTENT_DEG : float | None
        Half-width extent of domain in arc degrees.
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
    radius_earth = 6371000.0  # meters
    deg_to_km = (radius_earth / 1000.0) * (np.pi / 180.0)  # ~111.1949266 km/deg

    if EXTENT_KM is None:
        if EXTENT_DEG is not None:
            EXTENT_KM = EXTENT_DEG * deg_to_km
        else:
            raise ValueError(
                "Either EXTENT_KM or EXTENT_DEG must be provided for stereographic grid."
            )

    nx_val = NX if NX is not None else 1440
    ny_val = NY if NY is not None else 601
    x1d = np.linspace(-EXTENT_KM * 1000.0, EXTENT_KM * 1000.0, nx_val)
    y1d = np.linspace(-EXTENT_KM * 1000.0, EXTENT_KM * 1000.0, ny_val)

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

    if gtype == "regular":
        lon_start = kwargs.get("LON_START") if kwargs.get("LON_START") is not None else kwargs.get("lon_start")
        lat_start = kwargs.get("LAT_START") if kwargs.get("LAT_START") is not None else kwargs.get("lat_start")

        missing = []
        if lon_start is None:
            missing.append("LON_START / --lon-start")
        if lat_start is None:
            missing.append("LAT_START / --lat-start")

        if missing:
            raise ValueError(
                f"Missing mandatory parameter(s) for regular grid: {', '.join(missing)}"
            )

        lon_end = kwargs.get("LON_END") if kwargs.get("LON_END") is not None else kwargs.get("lon_end")
        lat_end = kwargs.get("LAT_END") if kwargs.get("LAT_END") is not None else kwargs.get("lat_end")

        sx = kwargs.get("SX") if kwargs.get("SX") is not None else kwargs.get("sx")
        if sx is None:
            sx = kwargs.get("DX") if kwargs.get("DX") is not None else kwargs.get("dx")
        if sx is None:
            sx = kwargs.get("DLON") if kwargs.get("DLON") is not None else kwargs.get("dlon")

        sy = kwargs.get("SY") if kwargs.get("SY") is not None else kwargs.get("sy")
        if sy is None:
            sy = kwargs.get("DY") if kwargs.get("DY") is not None else kwargs.get("dy")
        if sy is None:
            sy = kwargs.get("DLAT") if kwargs.get("DLAT") is not None else kwargs.get("dlat")

        if lon_end is None and sx is None:
            raise ValueError(
                "Missing mandatory parameter for regular grid: must provide either "
                "last longitude (LON_END / --lon-end) or longitude grid increment (SX / --sx)."
            )

        if lat_end is None and sy is None:
            raise ValueError(
                "Missing mandatory parameter for regular grid: must provide either "
                "last latitude (LAT_END / --lat-end) or latitude grid increment (SY / --sy)."
            )
        return

    elif gtype == "stereographic":
        missing = []
        for param in ("CENTER_LON", "CENTER_LAT"):
            val = kwargs.get(param) if kwargs.get(param) is not None else kwargs.get(param.lower())
            if val is None:
                missing.append(f"--{param.lower().replace('_', '-')}")

        ext_km = kwargs.get("EXTENT_KM") if kwargs.get("EXTENT_KM") is not None else kwargs.get("extent_km")
        ext_deg = kwargs.get("EXTENT_DEG") if kwargs.get("EXTENT_DEG") is not None else kwargs.get("extent_deg")
        if ext_km is None and ext_deg is None:
            missing.append("--extent-km or --extent-deg")

        if missing:
            raise ValueError(
                f"Missing mandatory parameter(s) for stereographic grid: {', '.join(missing)}"
            )
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
        - 'stereographic': General stereographic grid (via EXTENT_KM/RESOLUTION_KM or EXTENT_DEG/RESOLUTION_DEG).
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
