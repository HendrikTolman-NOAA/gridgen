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
# WAVEWATCH III (WW3) / WAVEWATCH IV (WW4) Command Line Interface module.

"""Command line interface for WAVEWATCH III (WW3) / WAVEWATCH IV (WW4) grid generation."""

from __future__ import annotations

import argparse

import numpy as np

from .grid import generate_grid
from .io.ascii import write_ww3file, write_ww3meta, write_ww3obstr
from .io.coards import nc_ww3_grdwrite
from .io.ugrid import create_ugrid_dataset, write_ugrid_nc
from .io.zarr_store import write_ugrid_zarr
from .masking import remove_lake
from .obstructions import create_obstr


def main() -> None:
    """CLI driver for grid generation and multi-format export."""
    parser = argparse.ArgumentParser(
        description="WAVEWATCH III (WW3) / WAVEWATCH IV (WW4) Grid Generation Tool"
    )
    parser.add_argument("--name", type=str, default="ww4_grid", help="Grid prefix name")
    parser.add_argument("--dx", type=float, default=0.25, help="Grid lon increment dx")
    parser.add_argument("--dy", type=float, default=0.25, help="Grid lat increment dy")
    parser.add_argument("--lon-start", type=float, default=140.0, help="Min longitude")
    parser.add_argument("--lon-end", type=float, default=160.0, help="Max longitude")
    parser.add_argument("--lat-start", type=float, default=44.0, help="Min latitude")
    parser.add_argument("--lat-end", type=float, default=54.0, help="Max latitude")
    parser.add_argument("--out-dir", type=str, default=".", help="Output directory")

    args = parser.parse_args()

    lon1d = np.arange(args.lon_start, args.lon_end + args.dx, args.dx)
    lat1d = np.arange(args.lat_start, args.lat_end + args.dy, args.dy)
    lon, lat = np.meshgrid(lon1d, lat1d)

    print(f"Generating grid '{args.name}' with shape {lon.shape}...")

    depth = generate_grid(lon, lat)
    m = np.ones_like(depth, dtype=int)
    m[depth == 999999.0] = 0

    m_mod, _ = remove_lake(m, lake_tol=-1, igl=0)
    sx, sy = create_obstr(lon, lat, [], m_mod)

    # 1. Legacy WW3 ASCII
    depth_scale = 1000.0
    obstr_scale = 100.0
    d_ascii = np.round(depth * depth_scale)
    write_ww3file(f"{args.out_dir}/{args.name}.depth_ascii", d_ascii)
    write_ww3file(f"{args.out_dir}/{args.name}.maskorig_ascii", m_mod)
    write_ww3obstr(
        f"{args.out_dir}/{args.name}.obstr_lev1",
        np.round(sx * obstr_scale),
        np.round(sy * obstr_scale),
    )
    write_ww3meta(
        f"{args.out_dir}/{args.name}",
        "RECT",
        lon,
        lat,
        1.0 / depth_scale,
        1.0 / obstr_scale,
        1.0,
    )

    # 2. Legacy GMT/NetCDF COARDS
    nc_ww3_grdwrite(
        lon, lat, depth, f"{args.out_dir}/{args.name}_coards.nc", mask=m_mod, sx=sx, sy=sy
    )

    # 3. WW4 NetCDF-UGRID 1.0
    ds_ugrid = create_ugrid_dataset(
        lon, lat, depth, m_mod, sx=sx, sy=sy, title=f"WW4 Grid {args.name}"
    )
    write_ugrid_nc(ds_ugrid, f"{args.out_dir}/{args.name}_ugrid.nc")

    # 4. WW4 Zarr Store
    write_ugrid_zarr(ds_ugrid, f"{args.out_dir}/{args.name}_ugrid.zarr")

    print("Successfully exported all grid formats (ASCII, COARDS NC, UGRID NC, Zarr)!")


if __name__ == "__main__":
    main()
