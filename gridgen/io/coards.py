# WAVEWATCH III (WW3) / WAVEWATCH IV (WW4) Gridgen Package
#
# Copyright 2026 National Weather Service (NWS), NOAA. All rights reserved.
# NWS often uses Generative AI (GenAI) for code development and refactoring.
# Whenever GenAI is used, NWS requires a full human review of code before it
# is added to its repositories.
#
# @file coards.py
# @brief Legacy GMT / NetCDF COARDS file writer for WAVEWATCH III / WAVEWATCH IV.
# @author Aldgisl (Agentic AI), Hendrik Tolman
# @author Jules (Agentic AI) (contributor)
# @date Initial: 2026-09-22
#
# Code Heritage:
# Converted from nc_ww3_grdwrite.m originally authored by Kelsey Jordahl
# and NOAA/NCEP (Arun Chawla).

"""Legacy GMT / NetCDF COARDS file writer for WAVEWATCH III (WW3) / WAVEWATCH IV (WW4)."""

from __future__ import annotations

from datetime import datetime, timezone

import numpy as np
import xarray as xr


def nc_ww3_grdwrite(
    x: np.ndarray,
    y: np.ndarray,
    z: np.ndarray,
    filename: str,
    fillval: float = np.nan,
    mask: np.ndarray | None = None,
    ObsX: np.ndarray | None = None,
    ObsY: np.ndarray | None = None,
    bathy_source: str = "etopo2",
) -> None:
    """Write GMT / COARDS compliant NetCDF grid file for WAVEWATCH III.

    Parameters
    ----------
    x : np.ndarray
        1D or 2D longitude array.
    y : np.ndarray
        1D or 2D latitude array.
    z : np.ndarray
        2D depth matrix array of shape (Ny, Nx).
    filename : str
        Target output NetCDF file path.
    fillval : float
        Fill value for missing data.
    mask : Optional[np.ndarray]
        2D land/sea mask array.
    ObsX : Optional[np.ndarray]
        2D subgrid obstruction in x direction.
    ObsY : Optional[np.ndarray]
        2D subgrid obstruction in y direction.
    """
    x_vec = x[0, :] if x.ndim == 2 else x
    y_vec = y[:, 0] if y.ndim == 2 else y

    data_vars = {
        "z": (
            ("lat", "lon"),
            z.astype(np.float32),
            {
                "long_name": "Depth",
                "_FillValue": np.float32(fillval),
                "scale_factor": 1.0,
                "add_offset": 0.0,
                "actual_range": [float(np.nanmin(z)), float(np.nanmax(z))],
            },
        )
    }

    if mask is not None:
        data_vars["mask"] = (
            ("lat", "lon"),
            mask.astype(np.float32),
            {
                "long_name": "mask",
                "_FillValue": np.float32(fillval),
                "scale_factor": 1.0,
                "add_offset": 0.0,
                "actual_range": [float(np.nanmin(mask)), float(np.nanmax(mask))],
            },
        )

    if ObsX is not None:
        data_vars["ObsX"] = (
            ("lat", "lon"),
            ObsX.astype(np.float32),
            {
                "long_name": "Subgrd obstr x",
                "_FillValue": np.float32(fillval),
                "scale_factor": 1.0,
                "add_offset": 0.0,
                "actual_range": [float(np.nanmin(ObsX)), float(np.nanmax(ObsX))],
            },
        )

    if ObsY is not None:
        data_vars["ObsY"] = (
            ("lat", "lon"),
            ObsY.astype(np.float32),
            {
                "long_name": "Subgrd obstr y",
                "_FillValue": np.float32(fillval),
                "scale_factor": 1.0,
                "add_offset": 0.0,
                "actual_range": [float(np.nanmin(ObsY)), float(np.nanmax(ObsY))],
            },
        )

    ds = xr.Dataset(
        data_vars=data_vars,
        coords={
            "lon": (
                "lon",
                x_vec.astype(np.float32),
                {
                    "long_name": "longitude",
                    "units": "degrees_east",
                    "actual_range": [float(np.min(x_vec)), float(np.max(x_vec))],
                },
            ),
            "lat": (
                "lat",
                y_vec.astype(np.float32),
                {
                    "long_name": "latitude",
                    "units": "degrees_north",
                    "actual_range": [float(np.min(y_vec)), float(np.max(y_vec))],
                },
            ),
        },
        attrs={
            "Conventions": "COARDS/CF-1.0",
            "title": filename,
            "source": "WAVEWATCH IV Gridgen Package",
            "bathy_source": bathy_source,
            "history": "File written by WAVEWATCH IV Python gridgen package",
            "description": f"Created {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')}",
            "GMT_version": "4.x",
        },
    )

    ds.to_netcdf(filename)
