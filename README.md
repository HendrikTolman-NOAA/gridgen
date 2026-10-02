<!--
# WAVEWATCH III (WW3) / WAVEWATCH IV (WW4) Gridgen Package
#
# Copyright 2026 National Weather Service (NWS), NOAA. All rights reserved.
# NWS often uses Generative AI (GenAI) for code development and refactoring.
# Whenever GenAI is used, NWS requires a full human review of code before it
# is added to its repositories.
#
# @author Aldgisl (Agentic AI), Jules (Agentic AI), Hendrik Tolman
# @date Initial: 2026-09-24
# @date Update: 2026-10-02
-->

<p align="center">
  <img src="https://github.com/NOAA-EMC/gridgen/wiki/images/WW_tools_banner.jpg" alt="WW_tools_banner" height="100">
</p>

# WAVEWATCH III (WW3) / WAVEWATCH IV (WW4) Gridgen Package

This software package is created for generating grids for WAVEWATCH III and WAVEWATCH IV.

## Documentation

Documentation is available at three levels:
1. Grid generation manual: `grid_generation.pdf` (can be found on the wiki page).
2. Comments in the scripts explaining what individual parts of the code are doing.
3. Brief explanations in each module and package subroutine.

## Installation

It is assumed that basic Python (v3.9 or higher) is installed already on your system.

To create a local clone of the repository:

```bash
git clone https://github.com/NOAA-EMC/gridgen.git
cd gridgen
```

It may be handy to add the root `gridgen` directory to your Python search path (`PYTHONPATH`):

```bash
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

Additionally, to execute utility scripts and binaries directly from any directory, you can add the root `gridgen` directory and its `bin/` sub-directory to your general shell search path (`PATH`):

```bash
export PATH="${PATH}:$(pwd):$(pwd)/bin"
```

### Reference Data Population

Large binary reference data files (such as NetCDF bathymetry models and coastal polygon datasets) are excluded from version control and must be placed in the `reference_data/` directory.

To pull in and populate the archive data, run the provided population script:

```bash
./populate_reference_data.sh [OPTIONS]
```

#### Script Options

The `populate_reference_data.sh` script supports the following command-line options:

| Option | Description |
| :--- | :--- |
| `-d, --target-dir DIR` | Specify target output directory (default: `./reference_data`). |
| `--legacy` | Pull legacy reference datasets (`etopo1.nc`, `etopo2.nc`, `coastal_bound_*.mat`). |
| `--etopo2022` | Pull newer NOAA NCEI ETOPO 2022 global relief model dataset (`ETOPO_2022_v1_60s_N90W180_bed.tif`). |
| `--gebco` | Display instructions and links for GEBCO global bathymetry grid. |
| `--gshhg` | Display instructions and links for GSHHG v2.3.7 vector shoreline database. |
| `--all` | Pull all available external datasets (legacy + ETOPO 2022) and display source information. |
| `-h, --help` | Display usage help message and exit. |

#### Default Behavior and Sources

When executed without dataset flags, the script defaults to retrieving legacy datasets. If legacy files are missing and the legacy server is unavailable, the script provides guidance and links for newer authoritative external sources (such as ETOPO 2022, GEBCO 2024, and GSHHG v2.3.7). The script automatically verifies existing datasets in the target directory and will not re-download or overwrite any file that is already present.

The reference dataset files include:
- NetCDF bathymetry files:
  - `etopo1.nc`
  - `etopo2.nc`
- Shoreline boundary polygon datasets:
  - `coastal_bound_coarse.mat`
  - `coastal_bound_high.mat`
  - `coastal_bound_low.mat`
  - `coastal_bound_full.mat`
  - `coastal_bound_inter.mat`
  - `optional_coastal_polygons.mat`

### Running Grid Generation Tool (`run_gridgen.sh`)

Once the reference data directory is populated, you can generate WAVEWATCH III and WAVEWATCH IV grid files using the provided `run_gridgen.sh` driver script:

```bash
./run_gridgen.sh [OPTIONS]
```

#### Script Options

| Option | Description |
| :--- | :--- |
| `-n, --name NAME` | Grid prefix identifier (default: `ww4_grid`). |
| `--dx DX` | Longitude grid resolution increment in degrees (default: `0.25`). |
| `--dy DY` | Latitude grid resolution increment in degrees (default: `0.25`). |
| `--lon-start LON` | Minimum longitude in degrees (default: `140.0`). |
| `--lon-end LON` | Maximum longitude in degrees (default: `160.0`). |
| `--lat-start LAT` | Minimum latitude in degrees (default: `44.0`). |
| `--lat-end LAT` | Maximum latitude in degrees (default: `54.0`). |
| `-o, --out-dir DIR` | Output directory for generated grid files (default: `.`). |
| `-r, --ref-dir DIR` | Reference data directory (default: `./reference_data`). |
| `-h, --help` | Display usage help message and exit. |

#### Output Formats

`run_gridgen.sh` invokes the Python grid generation pipeline (`gridgen.cli`) to generate the following grid file formats:
1. **Legacy WW3 ASCII grid**: `.depth_ascii`, `.maskorig_ascii`, `.obstr_lev1`, `.meta`
2. **Legacy GMT/NetCDF COARDS grid**: `_coards.nc`
3. **WW4 NetCDF-UGRID 1.0 grid**: `_ugrid.nc`
4. **WW4 Zarr Store grid**: `_ugrid.zarr`

## Dependencies

The package requires Python 3.9+ and the following scientific Python libraries:
- `numpy` (>= 1.20)
- `scipy` (>= 1.7)
- `xarray` (>= 2022.03)
- `netCDF4` (>= 1.5)
- `zarr` (>= 2.10)
- `shapely` (>= 2.0)

## Files

There are 3 sub-directories:
- `bin/`: Stores utility scripts and tools used in grid generation workflows.
- `examples/`: Stores examples of master scripts that call the different routines for creating grids.
- `reference_data/`: Stores reference data needed for creating grids, including global bathymetry datasets, GSHHS shoreline polygon databases, and optional user-defined polygon databases.

## Addendums

1. The `generate_grid` function now has two extra parameters that need to be set before the call can be made — a cut-off depth and a representative depth for dry cells.
2. A series of bugs were cleaned up:
   - Getting rid of spurious `NaN` values in `generate_grid`
   - Changing the algorithm in `compute_boundary` to remove errors associated with improper closing of certain boundaries
   - Speed up in the `clean_mask` routine
   - Generating grids only in the 0 - 360 lon range (this is the range in which the boundaries are defined, and switching to -180 - 180 range was leading to improper treatment of boundary closure in certain cases).

## Important

Gridgen now does not require the grids to be rectilinear to allow for development support for curvilinear grids. Thus lat / lon arrays are 2-dimensional to allow for varying resolution. Gridgen will not make the arrays needed for the grids. There are a number of software options available for that, but given the 2D arrays, Gridgen will generate all other features — bathymetry, masks, and obstruction grids. See examples for how to generate 2D grids.

---

**Last updated:** October 2, 2026

<p align="right">
  <img src="https://github.com/NOAA-EMC/gridgen/wiki/images/noaa_logo.gif" alt="NOAA Logo" height="50" width="55">
  <img src="https://github.com/NOAA-EMC/gridgen/wiki/images/nws.jpg" alt="NWS Logo" height="50" width="50">
</p>
