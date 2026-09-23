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
# WAVEWATCH IV Zarr chunked storage export module.

"""Zarr chunked store writer for WAVEWATCH IV UGRID datasets."""

from __future__ import annotations

from typing import Any

import xarray as xr


def write_ugrid_zarr(
    ds: xr.Dataset,
    store_path: str,
    chunks: dict[str, int] | None = None,
    mode: str = "w",
    **kwargs: Any,
) -> None:
    """Export NetCDF-UGRID xarray Dataset to a Zarr chunked store.

    Parameters
    ----------
    ds : xr.Dataset
        UGRID-compliant xarray Dataset.
    store_path : str
        Directory path or Zarr store URL.
    chunks : Optional[Dict[str, int]]
        Optional chunking specification dict (e.g. {'nMesh2_face': 1000}).
    mode : str
        Write mode ('w', 'w-', 'a').
    **kwargs : Any
        Additional keyword arguments passed to xarray.Dataset.to_zarr.
    """
    encoding = kwargs.pop("encoding", {})

    if chunks is not None:
        for var_name, var in ds.variables.items():
            var_chunks = []
            for dim in var.dims:
                if dim in chunks:
                    var_chunks.append(chunks[dim])
                else:
                    var_chunks.append(var.sizes[dim])
            if var_name not in encoding:
                encoding[var_name] = {}
            encoding[var_name]["chunks"] = tuple(var_chunks)

    ds.to_zarr(store_path, mode=mode, encoding=encoding, **kwargs)
