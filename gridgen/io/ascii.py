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
# Converted from write_ww3file.m, write_ww3obstr.m, write_ww3meta.m
# originally authored by NOAA/NCEP (Arun Chawla).

"""Legacy WAVEWATCH III ASCII file writers."""

from __future__ import annotations

import numpy as np


def write_ww3file(fname: str, data: np.ndarray) -> tuple[str, int]:
    """Write 2D matrix array into WAVEWATCH III ASCII file.

    Parameters
    ----------
    fname : str
        Output file path.
    data : np.ndarray
        2D numerical array of shape (Ny, Nx).

    Returns
    -------
    messg : str
        Error message string (empty if success).
    errno : int
        0 if successful, non-zero on error.
    """
    try:
        data_int = np.round(data).astype(int)
        with open(fname, "w") as f:
            f.writelines(" " + " ".join(map(str, row)) + " \n" for row in data_int)
        return "", 0
    except OSError as e:
        return str(e), 1


def write_ww3obstr(
    fname: str, d1: np.ndarray, d2: np.ndarray
) -> tuple[str, int]:
    """Write 2D subgrid obstruction arrays in x (d1) and y (d2) into ASCII file.

    Parameters
    ----------
    fname : str
        Output file path.
    d1 : np.ndarray
        2D obstruction array in x direction of shape (Ny, Nx).
    d2 : np.ndarray
        2D obstruction array in y direction of shape (Ny, Nx).

    Returns
    -------
    messg : str
        Error message string (empty if success).
    errno : int
        0 if successful, non-zero on error.
    """
    try:
        d1_int = np.round(d1).astype(int)
        d2_int = np.round(d2).astype(int)
        with open(fname, "w") as f:
            f.writelines(" " + " ".join(map(str, row)) + " \n" for row in d1_int)
            f.write("\n")
            f.writelines(" " + " ".join(map(str, row)) + " \n" for row in d2_int)
        return "", 0
    except OSError as e:
        return str(e), 1


def write_ww3meta(
    fname: str,
    gtype: str,
    lon: np.ndarray,
    lat: np.ndarray,
    n1: float = 1000.0,
    n2: float = 100.0,
    n3: float = 1.0,
    ext_depth: str = ".depth_ascii",
    ext_obstr: str = ".obstr_lev1",
    ext_mask: str = ".mask",
) -> tuple[str, int]:
    """Write metadata file (.meta) for WAVEWATCH III grid generation.

    Parameters
    ----------
    fname : str
        Output file path prefix (without or with .meta extension).
    gtype : str
        Grid type: 'RECT' (rectilinear) or 'CURV' (curvilinear).
    lon : np.ndarray
        2D longitude array of shape (Ny, Nx).
    lat : np.ndarray
        2D latitude array of shape (Ny, Nx).
    n1 : float
        Scaling applied to bottom bathymetry data.
    n2 : float
        Scaling applied to obstruction grids.
    n3 : float
        Scaling applied to coordinate grids.
    ext_depth : str
        Extension for depth file.
    ext_obstr : str
        Extension for obstruction file.
    ext_mask : str
        Extension for mask file.

    Returns
    -------
    messg : str
        Error message string (empty if success).
    errno : int
        0 if successful, non-zero on error.
    """
    meta_fname = fname if fname.endswith(".meta") else f"{fname}.meta"
    base_fname = fname.removesuffix(".meta")

    Ny, Nx = lon.shape

    lines = [
        "$ Define grid -------------------------------------- $",
        "$ Five records containing :",
        "$  1 Type of grid, coordinate system and type of closure: GSTRG, FLAGLL,",
        "$    CSTRG. Grid closure can only be applied in spherical coordinates.",
        "$      GSTRG  : String indicating type of grid :",
        "$               'RECT'  : rectilinear",
        "$               'CURV'  : curvilinear",
        "$      FLAGLL : Flag to indicate coordinate system :",
        "$               T  : Spherical (lon/lat in degrees)",
        "$               F  : Cartesian (meters)",
        "$      CSTRG  : String indicating the type of grid index space closure :",
        "$               'NONE'  : No closure is applied",
        "$               'SMPL'  : Simple grid closure : Grid is periodic in the",
        "$                         : i-index and wraps at i=NX+1. In other words,",
        "$                         : (NX+1,J) => (1,J). A grid with simple closure",
        "$                         : may be rectilinear or curvilinear.",
        "$               'TRPL'  : Tripole grid closure : Grid is periodic in the",
        "$                         : i-index and wraps at i=NX+1 and has closure at",
        "$                         : j=NY+1. In other words, (NX+1,J<=NY) => (1,J)",
        "$                         : and (I,NY+1) => (MOD(NX-I+1,NX)+1,NY). Tripole",
        "$                         : grid closure requires that NX be even. A grid",
        "$                         : with tripole closure must be curvilinear.",
        "$  2 NX, NY. As the outer grid lines are always defined as land",
        "$    points, the minimum size is 3x3.",
    ]

    gtype_upper = gtype.upper()
    if gtype_upper == "RECT":
        lines.extend((
            "$  3 Grid increments SX, SY (degr.or m) and scaling (division) factor.",
            "$    If NX*SX = 360., latitudinal closure is applied.",
            "$  4 Coordinates of (1,1) (degr.) and scaling (division) factor.",
        ))
    elif gtype_upper == "CURV":
        lines.extend((
            "$  3 Unit number of file with x-coordinate.",
            "$    Scale factor and add offset: x <= scale_fac * x_read + add_offset.",
            "$    IDLA, IDFM, format for formatted read, FROM and filename.",
            "$  4 Unit number of file with y-coordinate.",
            "$    Scale factor and add offset: y <= scale_fac * y_read + add_offset.",
            "$    IDLA, IDFM, format for formatted read, FROM and filename.",
        ))
    else:
        return f"Unrecognized grid type: {gtype}", 1

    lines.extend((
        "$  5 Limiting bottom depth (m) to discriminate between land and sea",
        "$    points, minimum water depth (m) as allowed in model, unit number",
        "$    of file with bottom depths, scale factor for bottom depths (mult.),",
        "$    IDLA, IDFM, format for formatted read, FROM and filename.",
        "$      IDLA : Layout indicator :",
        "$                  1   : Read line-by-line bottom to top.",
        "$                  2   : Like 1, single read statement.",
        "$                  3   : Read line-by-line top to bottom.",
        "$                  4   : Like 3, single read statement.",
        "$      IDFM : format indicator :",
        "$                  1   : Free format.",
        "$                  2   : Fixed format with above format descriptor.",
        "$                  3   : Unformatted.",
        "$      FROM : file type parameter",
        "$             'UNIT' : open file by unit number only.",
        "$             'NAME' : open file by name and assign to unit.",
        "$  If the Unit Numbers in above files is 10 then data is read from this file",
        "$",
        f"   '{gtype_upper}'  FLAGLL CSTRNG",
    ))

    if gtype_upper == "RECT":
        dx_min = (lon[0, 1] - lon[0, 0]) * 60.0 if Nx > 1 else 0.0
        dy_min = (lat[1, 0] - lat[0, 0]) * 60.0 if Ny > 1 else 0.0
        lines.append(f"{Nx} \t {Ny}")
        lines.append(f"{dx_min:5.2f} \t {dy_min:5.2f} \t 60.00")
        lines.append(f"{lon[0, 0]:8.4f} \t {lat[0, 0]:8.4f} \t 1.00")
    else:
        lines.append(f"{Nx} \t {Ny}")
        lines.append(
            f"20  {n3:f}  0.00  1  1 '(....)'  NAME  '{base_fname}.lon'"
        )
        lines.append(
            f"30  {n3:f}  0.00  1  1 '(....)'  NAME  '{base_fname}.lat'"
        )

    lines.extend((
        "$ Bottom Bathymetry",
        f"-0.10  2.50  40  {n1:f}  1  1 '(....)'  NAME  '{base_fname}{ext_depth}'",
        "$ Sub-grid information",
        f"50  {n2:f}  1  1 '(....)'  NAME  '{base_fname}{ext_obstr}'",
        "$ Mask Information",
        f"60  1  1 '(....)'  NAME  '{base_fname}{ext_mask}'",
    ))

    try:
        with open(meta_fname, "w") as f:
            f.writelines(line + "\n" for line in lines)
        return "", 0
    except OSError as e:
        return str(e), 1
