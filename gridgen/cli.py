# WAVEWATCH III (WW3) / WAVEWATCH IV (WW4) Gridgen Package
#
# Copyright 2026 National Weather Service (NWS), NOAA. All rights reserved.
# NWS often uses Generative AI (GenAI) for code development and refactoring.
# Whenever GenAI is used, NWS requires a full human review of code before it
# is added to its repositories.
#
# @file cli.py
# @brief Command line interface for WAVEWATCH III / WAVEWATCH IV grid generation.
# @author Aldgisl (Agentic AI), Hendrik Tolman
# @author Jules (Agentic AI) (contributor)
# @date Initial: 2026-09-22
# @date Latest Update: 2026-10-28
#
# Code Heritage:
# WAVEWATCH III (WW3) / WAVEWATCH IV (WW4) Command Line Interface module.

"""Command line interface for WAVEWATCH III (WW3) / WAVEWATCH IV (WW4) grid generation."""

from __future__ import annotations

import argparse
import os

import numpy as np

from .coordinates import create_grid_coordinates
from .grid import generate_grid
from .io.ascii import write_ww3file, write_ww3meta, write_ww3obstr
from .io.coards import nc_ww3_grdwrite
from .io.ugrid import create_ugrid_dataset, write_ugrid_nc
from .masking import (
    clean_mask,
    define_boundary_points,
    load_mat_polygons,
    load_user_polygons,
    remove_lake,
)
from .obstructions import create_obstr


def main() -> None:
    """CLI driver for grid generation and multi-format export."""
    parser = argparse.ArgumentParser(
        description="WAVEWATCH III (WW3) / WAVEWATCH IV (WW4) Grid Generation Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    # Group 1: General & Dimension Options (Common to all grid options)
    gen_group = parser.add_argument_group(
        "General & Dimension Parameters (Common to all grid options)"
    )
    gen_group.add_argument(
        "--nx",
        type=int,
        default=1440,
        metavar="NX",
        help="[Optional] Discrete grid dimension NX (number of X points, default: 1440)",
    )
    gen_group.add_argument(
        "--ny",
        type=int,
        default=601,
        metavar="NY",
        help="[Optional] Discrete grid dimension NY (number of Y points, default: 601)",
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
        "--bathy-source",
        type=str,
        default="etopo2",
        help="Bathymetry reference dataset identifier or filename prefix (default: etopo2)",
    )
    gen_group.add_argument(
        "--boundary-points",
        nargs="*",
        type=float,
        default=None,
        metavar="RANGE",
        help="Define input boundary cells (mask value 2) along regional grid boundaries, optionally specifying allowed range [LON_MIN LON_MAX LAT_MIN LAT_MAX]",
    )
    gen_group.add_argument(
        "--bound-file",
        dest="bound_file",
        type=str,
        default="coastal_bound_low.mat",
        metavar="FILE",
        help="MAT boundary polygon file path or name for subgrid obstructions, or 'none' to disable obstructions (default: coastal_bound_low.mat)",
    )
    gen_group.add_argument(
        "--local-polygons",
        action="store_true",
        help="Use optional user coastal polygon files from local directory (.) instead of gridgen_data",
    )
    gen_group.add_argument(
        "--no-user-polygons",
        action="store_true",
        help="Disable loading user coastal polygons (default: user polygons are loaded automatically)",
    )
    gen_group.add_argument(
        "--all-polygons",
        "--all-user-polygons",
        dest="all_polygons",
        action="store_true",
        help="Apply all coastal polygons independent of their actual flag values in user_polygons.flag",
    )
    gen_group.add_argument(
        "--user-flag",
        dest="flag_file",
        default=None,
        metavar="FILE",
        help="Custom user polygon switch control flag file path or name (default: user_polygons.flag)",
    )
    gen_group.add_argument(
        "--cut-off",
        "--cutoff-depth",
        type=float,
        default=0.1,
        metavar="DEPTH",
        help="Cut-off depth in meters to distinguish wet vs. dry cells (default: 0.1)",
    )
    gen_group.add_argument(
        "--lake-min-points",
        type=int,
        default=15,
        metavar="POINTS",
        help="Minimum number of grid points for a water body/lake to be retained (default: 15)",
    )
    gen_group.add_argument(
        "--lake-min-fraction",
        type=float,
        default=0.0005,
        metavar="FRACTION",
        help="Minimum fraction of total grid points for a water body/lake to be retained (default: 0.0005 [0.05%%])",
    )
    gen_group.add_argument(
        "--legacy",
        action="store_true",
        help="Export legacy WAVEWATCH III ASCII files and COARDS NetCDF file in addition to WW4 UGRID NC (default: False)",
    )

    # Group 2: Regular Grid Parameters
    reg_group = parser.add_argument_group("Regular Grid Parameters (--grid-type regular)")
    reg_group.add_argument(
        "--lon-start",
        type=float,
        default=0.0,
        metavar="LON_START",
        help="Lower-left corner longitude in degrees (default: 0.0)",
    )
    reg_group.add_argument(
        "--lat-start",
        type=float,
        default=-90.0,
        metavar="LAT_START",
        help="Lower-left corner latitude in degrees (default: -90.0)",
    )
    reg_group.add_argument(
        "--lon-end",
        type=float,
        default=None,
        metavar="LON_END",
        help="Upper-right corner longitude in degrees (default: 359.75)",
    )
    reg_group.add_argument(
        "--lat-end",
        type=float,
        default=None,
        metavar="LAT_END",
        help="Upper-right corner latitude in degrees (default: 90.0)",
    )
    reg_group.add_argument(
        "--sx",
        type=float,
        default=None,
        metavar="SX",
        help="Longitude grid increment in degrees (default: 0.25)",
    )
    reg_group.add_argument(
        "--sy",
        type=float,
        default=None,
        metavar="SY",
        help="Latitude grid increment in degrees (default: 0.3)",
    )
    reg_group.add_argument(
        "--pole-lon",
        type=float,
        default=0.0,
        metavar="POLE_LON",
        help="Longitude of rotated north pole in geographic coordinates (default: 0.0)",
    )
    reg_group.add_argument(
        "--pole-lat",
        type=float,
        default=90.0,
        metavar="POLE_LAT",
        help="Latitude of rotated north pole in geographic coordinates (default: 90.0)",
    )
    reg_group.add_argument(
        "--global-closure",
        "--global",
        dest="global_closure",
        action="store_true",
        help="Traditional regular grid with global closure (sx = 360/NX, lon_end calculated) (default: False)",
    )

    # Group 3: Stereographic Projection Parameters
    ste_group = parser.add_argument_group("Stereographic Grid Parameters (--grid-type stereographic)")
    ste_group.add_argument(
        "--center-lon",
        type=float,
        default=0.0,
        metavar="CENTER_LON",
        help="Projection center longitude in degrees (default: 0.0)",
    )
    ste_group.add_argument(
        "--center-lat",
        type=float,
        default=90.0,
        metavar="CENTER_LAT",
        help="Projection center latitude in degrees (default: 90.0)",
    )
    ste_group.add_argument(
        "--extent-km",
        type=float,
        default=1000.0,
        metavar="EXTENT_KM",
        help="Half-width domain extent in kilometers (default: 1000.0)",
    )
    ste_group.add_argument(
        "--extent-deg",
        type=float,
        default=None,
        metavar="EXTENT_DEG",
        help="Half-width domain extent in arc degrees (default: None)",
    )
    ste_group.add_argument(
        "--rotation",
        type=float,
        default=0.0,
        metavar="ROTATION",
        help="Grid rotation angle in degrees on projection plane (default: 0.0)",
    )

    # Group 4: Custom Grid File Parameters
    cus_group = parser.add_argument_group("Custom Grid Parameters (--grid-type custom)")
    cus_group.add_argument(
        "--custom-grid",
        type=str,
        default=None,
        metavar="CUSTOM_GRID",
        help="Path to custom grid layout file (.nc, .npz, .npy, .mat, .dat, .txt, .csv) (default: None)",
    )

    args = parser.parse_args()

    # Step 1: Create 2D grid coordinates array
    print(f"[Step 1/5] Generating 2D '{args.grid_type}' grid coordinates for '{args.name}'...")
    lon, lat = create_grid_coordinates(**vars(args))
    print(f"  Grid matrix dimensions: NY={lon.shape[0]}, NX={lon.shape[1]}")

    # Step 2: Extract bathymetry
    print(f"[Step 2/5] Extracting bathymetry depths from '{args.bathy_source}' dataset...")
    depth = generate_grid(
        lon,
        lat,
        ref_dir=args.ref_dir,
        bathy_source=args.bathy_source,
        cut_off=args.cut_off,
    )

    wet_mask = depth <= args.cut_off
    land_mask = (depth > args.cut_off) & (depth < 999999.0)

    if np.any(wet_mask):
        min_wdepth = float(-np.max(depth[wet_mask]))
        max_wdepth = float(-np.min(depth[wet_mask]))
        wdepth_str = f"{min_wdepth:.1f} m to {max_wdepth:.1f} m"
    else:
        wdepth_str = "None (no water cells)"

    if np.any(land_mask):
        min_lheight = float(np.min(depth[land_mask]))
        max_lheight = float(np.max(depth[land_mask]))
        lheight_str = f"{min_lheight:.1f} m to {max_lheight:.1f} m"
    else:
        lheight_str = "None (no land height data)"

    print(f"  Water depth range: {wdepth_str}")
    print(f"  Land height range: {lheight_str}")

    m = np.where(depth <= args.cut_off, 1, 0)

    # Resolve boundary MAT file (default: coastal_bound_low.mat; 'none' disables obstructions)
    mat_bounds = []
    if args.bound_file and args.bound_file.lower() != "none":
        candidates = [
            args.bound_file,
            os.path.join(args.ref_dir, args.bound_file),
            os.path.join(".", args.bound_file),
            os.path.join("reference_data", args.bound_file),
        ]
        target_bound_file = None
        for c in candidates:
            if os.path.exists(c):
                target_bound_file = c
                break

        if target_bound_file and os.path.exists(target_bound_file):
            mat_bounds = load_mat_polygons(target_bound_file)
            if mat_bounds:
                print(f"Loaded {len(mat_bounds)} boundary polygons from '{target_bound_file}'.")
    else:
        print("Subgrid obstruction generation disabled (--bound-file set to 'none').")

    user_bounds = []
    if not args.no_user_polygons:
        poly_dir = "." if args.local_polygons else "gridgen_data"
        user_bounds = load_user_polygons(
            ref_dir=poly_dir,
            flag_file=args.flag_file,
            all_polygons=args.all_polygons,
        )
        if user_bounds:
            print(f"Loaded {len(user_bounds)} active user-defined coastal polygons.")

    if user_bounds:
        m = clean_mask(lon, lat, m, user_bounds)

    # Step 3: Land/Sea Masking & Lake Removal
    print("[Step 3/5] Generating land/sea mask and applying lake removal...")
    print(
        f"  Lake removal threshold settings: {args.lake_min_points}, "
        f"{args.lake_min_fraction} ({args.lake_min_fraction * 100.0:.2f}%)"
    )
    m_mod, _ = remove_lake(
        m,
        min_lake_points=args.lake_min_points,
        min_lake_fraction=args.lake_min_fraction,
        igl=0,
        lon=lon,
    )
    if args.boundary_points is not None:
        if len(args.boundary_points) in (0, 4):
            b_range = tuple(args.boundary_points) if len(args.boundary_points) == 4 else None
            m_mod = define_boundary_points(m_mod, lon, lat, bound_range=b_range)
        else:
            parser.error(
                f"--boundary-points expects 0 arguments or 4 arguments [LON_MIN LON_MAX LAT_MIN LAT_MAX], got {len(args.boundary_points)}"
            )

    num_bnd = int(np.count_nonzero(m_mod == 2))
    if num_bnd > 0:
        print(f"  Boundary points generated: {num_bnd} (mask value 2).")
    else:
        print("  No boundary points generated.")

    # Step 4: Calculate sub-grid obstructions (using shoreline MAT bounds only; user polygons reserved for mask generation)
    print("[Step 4/5] Computing directional sub-grid obstruction factors (ObsX, ObsY)...")
    ObsX, ObsY = create_obstr(lon, lat, mat_bounds, m_mod)

    # Step 5: Export NetCDF-UGRID 1.0 (Default Output)
    print("[Step 5/5] Exporting WW4 NetCDF-UGRID 1.0 grid dataset...")
    ds_ugrid = create_ugrid_dataset(
        lon,
        lat,
        depth,
        m_mod,
        ObsX=ObsX,
        ObsY=ObsY,
        title=f"WW4 Grid {args.name}",
        bathy_source=args.bathy_source,
        bound_source=args.bound_file,
    )
    nc_path = f"{args.out_dir}/{args.name}_ugrid.nc"
    write_ugrid_nc(ds_ugrid, nc_path)

    if args.legacy:
        print("  Exporting legacy WW3 ASCII and COARDS NetCDF grid files...")
        depth_scale = 1000.0
        obstr_scale = 100.0
        d_ascii = np.round(depth * depth_scale)
        write_ww3file(f"{args.out_dir}/{args.name}.depth_ascii", d_ascii)
        write_ww3file(f"{args.out_dir}/{args.name}.maskorig_ascii", m_mod)
        write_ww3obstr(
            f"{args.out_dir}/{args.name}.obstr_lev1",
            np.round(ObsX * obstr_scale),
            np.round(ObsY * obstr_scale),
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
        nc_ww3_grdwrite(
            lon,
            lat,
            depth,
            f"{args.out_dir}/{args.name}_coards.nc",
            mask=m_mod,
            ObsX=ObsX,
            ObsY=ObsY,
            bathy_source=args.bathy_source,
            bound_source=args.bound_file,
        )

    print("Successfully generated WW4 NetCDF-UGRID grid output!")


if __name__ == "__main__":
    main()
