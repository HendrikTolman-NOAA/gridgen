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
# @date Latest Update: 2026-10-07
#
# Code Heritage:
# WAVEWATCH III (WW3) / WAVEWATCH IV (WW4) Command Line Interface module.

"""Command line interface for WAVEWATCH III (WW3) / WAVEWATCH IV (WW4) grid generation."""

from __future__ import annotations

import argparse

import numpy as np

from .coordinates import create_grid_coordinates
from .grid import generate_grid
from .io.ascii import write_ww3file, write_ww3meta, write_ww3obstr
from .io.coards import nc_ww3_grdwrite
from .io.ugrid import create_ugrid_dataset, write_ugrid_nc
from .masking import clean_mask, define_boundary_points, load_user_polygons, remove_lake
from .obstructions import create_obstr


def main() -> None:
    """CLI driver for grid generation and multi-format export."""
    parser = argparse.ArgumentParser(
        description="WAVEWATCH III (WW3) / WAVEWATCH IV (WW4) Grid Generation Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    # Group 1: General & Dimension Options (Meaningful for all grid types)
    gen_group = parser.add_argument_group(
        "General & Dimension Parameters (Common to all grid types)"
    )
    gen_group.add_argument(
        "--nx",
        type=int,
        default=None,
        help="[Mandatory/Recommended] Discrete grid dimension NX (number of longitude/X grid points)",
    )
    gen_group.add_argument(
        "--ny",
        type=int,
        default=None,
        help="[Mandatory/Recommended] Discrete grid dimension NY (number of latitude/Y grid points)",
    )
    gen_group.add_argument(
        "--name", type=str, default="ww4_grid", help="Grid prefix identifier (default: ww4_grid)"
    )
    gen_group.add_argument(
        "--grid-type",
        type=str,
        default="regular",
        choices=[
            "regular",
            "stereographic",
            "polar_stereographic",
            "lambert_conformal",
            "rotated_pole",
            "custom",
        ],
        help="Grid coordinate projection/layout type (default: regular)",
    )
    gen_group.add_argument(
        "--out-dir", type=str, default=".", help="Output directory for generated files (default: .)"
    )
    gen_group.add_argument(
        "--ref-dir", type=str, default="reference_data", help="Reference data directory (default: reference_data)"
    )
    gen_group.add_argument(
        "--boundary-points",
        action="store_true",
        help="Define input boundary points (mask value 2) along regional grid boundaries",
    )
    gen_group.add_argument(
        "--user-polygons-flag",
        type=str,
        default=None,
        help="Path to flag file for optional user coastal polygons (optional_coastal_polygons.mat)",
    )

    # Group 2: Regular Grid Parameters
    reg_group = parser.add_argument_group("Regular Grid Parameters (--grid-type regular)")
    reg_group.add_argument(
        "--sx", "--dx", dest="sx", type=float, default=None, help="Grid longitude increment/spacing in degrees (SX/DX)"
    )
    reg_group.add_argument(
        "--sy", "--dy", dest="sy", type=float, default=None, help="Grid latitude increment/spacing in degrees (SY/DY)"
    )
    reg_group.add_argument(
        "--lon-start", type=float, default=None, help="Lower-left corner longitude in degrees"
    )
    reg_group.add_argument(
        "--lat-start", type=float, default=None, help="Lower-left corner latitude in degrees"
    )
    reg_group.add_argument(
        "--lon-end", type=float, default=None, help="Upper-right corner longitude in degrees"
    )
    reg_group.add_argument(
        "--lat-end", type=float, default=None, help="Upper-right corner latitude in degrees"
    )

    # Group 3: Rotated Pole Grid Parameters
    rot_group = parser.add_argument_group("Rotated Pole Grid Parameters (--grid-type rotated_pole)")
    rot_group.add_argument(
        "--pole-lon",
        type=float,
        default=None,
        help="[Mandatory] Longitude of rotated north pole in geographic coordinates",
    )
    rot_group.add_argument(
        "--pole-lat",
        type=float,
        default=None,
        help="[Mandatory] Latitude of rotated north pole in geographic coordinates",
    )

    # Group 4: Stereographic Projection Parameters
    ste_group = parser.add_argument_group("Stereographic Grid Parameters (--grid-type stereographic)")
    ste_group.add_argument(
        "--center-lon",
        type=float,
        default=None,
        help="[Mandatory] Projection center longitude in degrees (also anchor point for regular/rotated grids)",
    )
    ste_group.add_argument(
        "--center-lat",
        type=float,
        default=None,
        help="[Mandatory] Projection center latitude in degrees (also anchor point for regular/rotated grids)",
    )
    ste_group.add_argument(
        "--extent-km",
        type=float,
        default=None,
        help="[Mandatory] Half-width domain extent in kilometers",
    )
    ste_group.add_argument(
        "--resolution-km",
        type=float,
        default=None,
        help="[Mandatory] Grid resolution in kilometers",
    )

    # Group 5: Lambert Conformal Conic Parameters
    lam_group = parser.add_argument_group("Lambert Conformal Conic Parameters (--grid-type lambert_conformal)")
    lam_group.add_argument(
        "--lat-1",
        type=float,
        default=None,
        help="[Mandatory] First standard parallel in degrees",
    )
    lam_group.add_argument(
        "--lat-2",
        type=float,
        default=None,
        help="[Mandatory] Second standard parallel in degrees",
    )

    # Group 6: Custom Grid File Parameters
    cus_group = parser.add_argument_group("Custom Grid Parameters (--grid-type custom)")
    cus_group.add_argument(
        "--custom-grid",
        type=str,
        default=None,
        help="[Mandatory] Path to custom grid layout file (.nc, .npz, .npy, .mat, .dat, .txt, .csv)",
    )

    args = parser.parse_args()

    # Step 1: Create 2D grid coordinates array
    lon, lat = create_grid_coordinates(**vars(args))

    print(f"Generating '{args.grid_type}' grid '{args.name}' with shape {lon.shape}...")

    # Step 2: Extract bathymetry & generate mask and obstructions
    depth = generate_grid(lon, lat, ref_dir=args.ref_dir)
    m = np.ones_like(depth, dtype=int)
    m[depth == 999999.0] = 0

    user_bounds = []
    if args.user_polygons_flag:
        user_bounds = load_user_polygons(
            ref_dir=args.ref_dir, flag_file=args.user_polygons_flag
        )
        if user_bounds:
            print(f"Loaded {len(user_bounds)} active user-defined coastal polygons.")
            m = clean_mask(lon, lat, m, user_bounds)

    m_mod, _ = remove_lake(m, lake_tol=-1, igl=0)
    if args.boundary_points:
        m_mod = define_boundary_points(m_mod, lon, lat)

    sx, sy = create_obstr(lon, lat, user_bounds, m_mod)

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
        lon,
        lat,
        depth,
        f"{args.out_dir}/{args.name}_coards.nc",
        mask=m_mod,
        sx=sx,
        sy=sy,
    )

    # 3. WW4 NetCDF-UGRID 1.0
    ds_ugrid = create_ugrid_dataset(
        lon, lat, depth, m_mod, sx=sx, sy=sy, title=f"WW4 Grid {args.name}"
    )
    write_ugrid_nc(ds_ugrid, f"{args.out_dir}/{args.name}_ugrid.nc")

    print("Successfully exported all grid formats (ASCII, COARDS NC, UGRID NC)!")


if __name__ == "__main__":
    main()
