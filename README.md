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
# @date Latest Update: 2026-10-28
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

## Dependencies

The package requires Python 3.9+ and the following scientific Python libraries:
- `numpy` (>= 1.20)
- `scipy` (>= 1.7)
- `xarray` (>= 2022.03)
- `netCDF4` (>= 1.5)
- `shapely` (>= 2.0)
- `matplotlib` (>= 3.5)

For building the optional C++ reader library (`ww4_ugrid_reader`), metadata inspection tools (`ww4_read_grid`), and unit tests, the following system packages or submodules are required:
- C++20 compliant compiler (`GCC 11+` or `Clang 13+`)
- `CMake` (>= 3.20)
- `libnetcdf-dev` (NetCDF C development library, or included via `externals/netcdf-c`)
- `libgtest-dev` (GoogleTest development headers, or included via `externals/googletest`)

## Installation

It is assumed that basic Python (v3.9 or higher) is installed already on your system.

To create a local clone of the repository and automatically pull external Git submodules into `externals/`:

```bash
git clone --recursive https://github.com/NOAA-EMC/gridgen
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

## External Submodules (`externals/`)

All third-party external C++ dependencies managed as Git submodules are located in the `externals/` directory:
- **`externals/netcdf-c`**: Unidata NetCDF-C library for NetCDF-4 file I/O operations.
- **`externals/googletest`**: GoogleTest framework for C++ unit testing.

### Loading External Submodules Before Compilation

Before compiling the C++ toolchain or running CMake, you **must ensure that all external submodules in `externals/` are fetched and initialized**.

If you cloned the repository without the `--recursive` flag, initialize and load all externals by running:

```bash
git submodule update --init --recursive
```

To verify that all external submodules in `externals/` are properly populated before building:

```bash
git submodule status
```

You should see commit hashes for both `externals/netcdf-c` and `externals/googletest` without a leading minus sign (`-`).

## Building and Compiling C++ Tools

The repository contains a C++20 NetCDF-UGRID reader library (`ww4_ugrid_reader`), a grid metadata printer utility program (`ww4_read_grid`), and GoogleTest unit tests.

### Prerequisites (Ubuntu / Debian)

System libraries are optional if submodules in `externals/` are populated:

```bash
sudo apt-get update
sudo apt-get install -y build-essential cmake libnetcdf-dev libgtest-dev
```

### Build Instructions

First, ensure external submodules in `externals/` are fetched (`git submodule update --init --recursive`), then build the C++ static library, metadata utility binary, and unit test runner using CMake:

```bash
cmake -B build -S . -DCMAKE_BUILD_TYPE=Release
cmake --build build
```

The CMake build automatically checks for system libraries first and seamlessly falls back to using `externals/netcdf-c` and `externals/googletest` submodules when system libraries are missing.

This compiles the following targets in the `build/` directory:
- `libww4_ugrid_reader.a`: C++ static library providing `ww4::io::read_ugrid_nc()`.
- `ww4_read_grid`: Executable metadata inspection program.
- `test_ugrid_reader`: C++ GoogleTest suite.

### Running C++ Metadata Printer Utility (`ww4_read_grid`)

To inspect global metadata attributes, grid dimensions, bathymetry depth ranges, land/sea cell counts, and obstruction availability of any NetCDF-UGRID grid file:

```bash
./build/ww4_read_grid <path_to_grid_file.nc>
```

Example usage:

```bash
./build/ww4_read_grid ww4_grid_ugrid.nc
```

### Running C++ Unit Tests

Execute the C++ test suite using CTest:

```bash
ctest --test-dir build --output-on-failure
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
| `--etopo2022` | Pull newer NOAA NCEI ETOPO 2022 global relief model NetCDF dataset (`etopo_2022.nc`). |
| `--gebco` | Pull GEBCO global bathymetry grid NetCDF dataset (`gebco_2024.nc`). |
| `--gshhg` | Pull GSHHG v2.3.7 vector shoreline database (`gshhg-bin-2.3.7.zip`). |
| `--all` | Pull all available external datasets (legacy + ETOPO 2022, GEBCO, GSHHG). |
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

### User-Defined Coastal Polygons (`gridgen_data/`)

Optional user-defined coastal polygon coordinates (`optional_coastal_polygons.txt`) and polygon switch control file (`user_polygons.flag`) are unique to the tool and maintained directly in the repository in `gridgen_data/`. They allow users to explicitly mask out water bodies (such as inland lakes, bays, or estuaries) that do not play a significant role in wave propagation. User polygons in `gridgen_data/` are automatically loaded by default:
- `load_user_polygons(ref_dir="gridgen_data", flag_file=...)` loads and filters active user boundary polygons based on the control switches (`0` = off, `1` = on).
- Active user polygons are passed into `clean_mask()` to refine land/sea mask boundaries and `create_obstr()` to calculate directional sub-grid obstruction factors ($\text{ObsX}$, $\text{ObsY}$).
- To use custom polygon files in the current/local directory (`.`), pass `--local-polygons`. Local polygon files appearing in the root directory of the clone (`user_polygons.flag`, `optional_coastal_polygons.txt`, `optional_coastal_polygons.mat`) are ignored by Git.
- To disable user polygon masking completely, pass `--no-user-polygons`.
- To apply all coastal polygons independent of their switch flag values in `user_polygons.flag`, pass `--all-polygons`.

### Running Grid Generation Tool (`run_gridgen.sh`)

Once the reference data directory is populated, you can generate WAVEWATCH III and WAVEWATCH IV grid files using the provided `run_gridgen.sh` driver script:

```bash
./run_gridgen.sh [OPTIONS]
```

#### Script Options

| Option | Description |
| :--- | :--- |
| `--nx NX` | Discrete grid dimension NX (default: `1440`). Common to all grid options. `[Optional]` |
| `--ny NY` | Discrete grid dimension NY (default: `601`). Common to all grid options. `[Optional]` |
| `-n, --name NAME` | Grid prefix identifier (default: `ww4_grid`). `[Optional]` |
| `-g, --grid-type TYPE` | Grid coordinate projection/layout type: `regular`, `stereographic`, `custom` (default: `regular`). `[Optional]` |
| `--bathy-source SOURCE` | Bathymetry dataset identifier or NetCDF prefix (e.g. `etopo1`, `etopo2`, `ETOPO_2022_v1_60s_N90W180_bed`) (default: `etopo2`). `[Optional]` |
| `--boundary-points` | Define input boundary cells (mask value 2) along regional grid boundaries. `[Optional]` |
| `--local-polygons` | Use user coastal polygon files from local directory (`.`) instead of `gridgen_data`. Local polygon files in root clone directory are not tracked in Git. `[Optional]` |
| `--no-user-polygons` | Disable loading user coastal polygons (loaded automatically by default). `[Optional]` |
| `--all-polygons` | Apply all coastal polygons independent of their switch values in `user_polygons.flag`. `[Optional]` |
| `--lon-start LON` | Lower-left corner longitude in degrees. `[Mandatory for regular grid]` |
| `--lat-start LAT` | Lower-left corner latitude in degrees. `[Mandatory for regular grid]` |
| `--lon-end LON` | Upper-right corner longitude in degrees. `[Mandatory if --sx omitted]` |
| `--lat-end LAT` | Upper-right corner latitude in degrees. `[Mandatory if --sy omitted]` |
| `--sx SX` | Longitude grid increment in degrees. `[Mandatory if --lon-end omitted]` |
| `--sy SY` | Latitude grid increment in degrees. `[Mandatory if --lat-end omitted]` |
| `--pole-lon LON` | Rotated north pole longitude in degrees. `[Optional for regular grid]` |
| `--pole-lat LAT` | Rotated north pole latitude in degrees (reverts to regular grid when lat is 90.0). `[Optional for regular grid]` |
| `--center-lon LON` | Center longitude for stereographic projection in degrees. `[Mandatory for stereographic grid]` |
| `--center-lat LAT` | Center latitude for stereographic projection in degrees. `[Mandatory for stereographic grid]` |
| `--extent-km KM` | Half-width domain extent in km for stereographic grid. `[Mandatory if --extent-deg omitted]` |
| `--extent-deg DEG` | Half-width domain extent in arc degrees for stereographic grid. `[Mandatory if --extent-km omitted]` |
| `--rotation ROTATION` | Grid rotation angle in degrees on stereographic projection plane (default: `0.0`). `[Optional for stereographic grid]` |
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

A graphical display shell driver script is provided in the repository root directory to generate plot graphics of bathymetry depth and land-sea masks overlaid with sub-grid directional obstruction factors ($\text{ObsX}$, $\text{ObsY}$) and three colorbar legends:

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
| `--title TITLE` | Custom main figure title (default: input dataset filename). |
| `--no-title` | Disable main figure title. |
| `--subtitle SUBTITLE` | Custom figure subtitle (default: `Bathymetry, Orography, and Obstructions`). |
| `--no-subtitle` | Disable figure subtitle. |
| `--no-mask` | Disable land-sea mask display. |
| `--zoom LON LAT FACTOR` | Zoom view centered at central longitude and latitude with zoom factor (e.g. `--zoom -70 40 2`). |
| `--max-depth DEPTH` | Maximum depth limit for color scale (default: `-8000`). |

---

**Last updated:** October 28, 2026

<p align="right">
  <img src="https://github.com/NOAA-EMC/gridgen/wiki/images/noaa_logo.gif" alt="NOAA Logo" height="50" width="55">
  <img src="https://github.com/NOAA-EMC/gridgen/wiki/images/nws.jpg" alt="NWS Logo" height="50" width="50">
</p>
