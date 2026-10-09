<!--
# WAVEWATCH III (WW3) / WAVEWATCH IV (WW4) Gridgen Package
#
# Copyright 2026 National Weather Service (NWS), NOAA. All rights reserved.
# NWS often uses Generative AI (GenAI) for code development and refactoring.
# Whenever GenAI is used, NWS requires a full human review of code before it
# is added to its repositories.
#
# @author Aldgisl (Agentic AI), Hendrik Tolman
# @author Jules (Agentic AI) (contributor)
# @date Initial: 2026-09-24
# @date Latest Update: 2026-10-09
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
git clone https://github.com/NOAA-EMC/gridgen
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
| `-c, --clean, --cleanup` | Remove all reference dataset files from the target directory. |
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

### User-Defined Coastal Polygons

Optional user-defined coastal polygons (`optional_coastal_polygons.mat`) allow users to explicitly mask out water bodies (such as inland lakes, bays, or estuaries) that do not play a significant role in wave propagation. User polygon selection is controlled by a flag text file (e.g. `user_polygons.flag`) containing binary switches (0 = off, 1 = on) per polygon index:
- `load_user_polygons(ref_dir, flag_file)` loads and filters active user boundary polygons based on the control switches.
- Active user polygons are passed into `clean_mask()` to refine land/sea mask boundaries and `create_obstr()` to calculate directional sub-grid obstruction factors ($S_x$, $S_y$).

### Running Grid Generation Tool (`run_gridgen.sh`)

Once the reference data directory is populated, you can generate WAVEWATCH III and WAVEWATCH IV grid files using the provided `run_gridgen.sh` driver script:

```bash
./run_gridgen.sh [OPTIONS]
```

#### Script Options

| Option | Description |
| :--- | :--- |
| `--nx NX` | Discrete grid dimension NX (default: `401`). Common to all grid options. `[Optional]` |
| `--ny NY` | Discrete grid dimension NY (default: `125`). Common to all grid options. `[Optional]` |
| `-n, --name NAME` | Grid prefix identifier (default: `ww4_grid`). `[Optional]` |
| `-g, --grid-type TYPE` | Grid coordinate projection/layout type: `regular`, `stereographic`, `custom` (default: `regular`). `[Optional]` |
| `--lon-start LON` | Lower-left corner longitude in degrees. `[Mandatory for regular grid]` |
| `--lat-start LAT` | Lower-left corner latitude in degrees. `[Mandatory for regular grid]` |
| `--lon-end LON` | Upper-right corner longitude in degrees. `[Mandatory for regular grid]` |
| `--lat-end LAT` | Upper-right corner latitude in degrees. `[Mandatory for regular grid]` |
| `--pole-lon LON` | Rotated north pole longitude in degrees. `[Optional for regular grid]` |
| `--pole-lat LAT` | Rotated north pole latitude in degrees (reverts to regular grid when lat is 90.0). `[Optional for regular grid]` |
| `--center-lon LON` | Center longitude for stereographic projection in degrees. `[Mandatory for stereographic grid]` |
| `--center-lat LAT` | Center latitude for stereographic projection in degrees. `[Mandatory for stereographic grid]` |
| `--extent-km KM` | Half-width domain extent in km for stereographic grid. `[Mandatory if --extent-deg omitted]` |
| `--resolution-km KM` | Grid resolution in km for stereographic grid. `[Optional]` |
| `--extent-deg DEG` | Half-width domain extent in arc degrees for stereographic grid. `[Mandatory if --extent-km omitted]` |
| `--resolution-deg DEG` | Grid resolution in arc degrees for stereographic grid. `[Optional]` |
| `--custom-grid FILE` | Path to custom grid layout file (`.nc`, `.npz`, `.npy`, `.mat`, `.dat`, `.txt`, `.csv`). `[Mandatory for custom grid]` |
| `-o, --out-dir DIR` | Output directory for generated grid files (default: `.`). `[Optional]` |
| `-r, --ref-dir DIR` | Reference data directory (default: `./reference_data`). `[Optional]` |
| `-c, --clean, --cleanup` | Remove generated output grid files and graphics files for specified `--name` from output directory. `[Optional]` |
| `-h, --help` | Display usage help message and exit. `[Optional]` |

#### Output Formats

`run_gridgen.sh` invokes the Python grid generation pipeline (`gridgen.cli`) to generate the following grid file formats:
1. **Legacy WW3 ASCII grid**: `.depth_ascii`, `.maskorig_ascii`, `.obstr_lev1`, `.meta`
2. **Legacy GMT/NetCDF COARDS grid**: `_coards.nc`
3. **WW4 NetCDF-UGRID 1.0 grid**: `_ugrid.nc`

### Grid & Obstruction Visualization (`plot_grid.sh`)

A graphical display shell driver script is provided in the repository root directory to generate multi-panel plot graphics of bathymetry depth, land-sea masks, and sub-grid directional obstruction factors ($S_x$, $S_y$):

```bash
./plot_grid.sh [OPTIONS]
```

Or via the utility binary or installed package CLI entry point:

```bash
./bin/plot_grid.py -i ww4_grid_ugrid.nc -f jpg -o ww4_grid.jpg
ww4plotgrid -i ww4_grid_ugrid.nc -f pdf -o ww4_grid.pdf
```

#### Script Options

| Option | Description |
| :--- | :--- |
| `-i, --input PATH` | Input grid dataset filepath (`_ugrid.nc`, `_coards.nc`, or ASCII prefix). Default: `ww4_grid_ugrid.nc`. |
| `-o, --output PATH` | Output figure image path. Default: `<GRIDNAME>.<format>` (e.g. `ww4_grid.jpg`). |
| `-f, --format FORMAT` | Output graphic format: `jpg`, `png`, `pdf`, `eps`, or `gif`. Default: `jpg`. |
| `--title TITLE` | Custom title for the generated figure. |
| `--display` | Interactively display figure window (default: enabled). |
| `--no-display` | Disable interactive figure window display. |

To display the generated grid plot image in the present window:

```bash
./view_grid.sh [IMAGE_FILE]
```

## Dependencies

The package requires Python 3.9+ and the following scientific Python libraries:
- `numpy` (>= 1.20)
- `scipy` (>= 1.7)
- `xarray` (>= 2022.03)
- `netCDF4` (>= 1.5)
- `shapely` (>= 2.0)
- `matplotlib` (>= 3.5)

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

**Last updated:** October 9, 2026

<p align="right">
  <img src="https://github.com/NOAA-EMC/gridgen/wiki/images/noaa_logo.gif" alt="NOAA Logo" height="50" width="55">
  <img src="https://github.com/NOAA-EMC/gridgen/wiki/images/nws.jpg" alt="NWS Logo" height="50" width="50">
</p>
