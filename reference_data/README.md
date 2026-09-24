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
-->

# WAVEWATCH III (WW3) / WAVEWATCH IV (WW4) Gridgen Reference Data

This directory (`reference_data/`) contains the reference bathymetry datasets, shoreline polygon databases, and regional mask configuration files required by the WAVEWATCH III and WAVEWATCH IV grid generation (`ww4gridgen`) software.

Due to file size constraints, large binary datasets (`.nc`, `.tif`, and `.mat` files) are excluded from version control via `.gitignore` and must be provided or populated prior to grid generation.

A automated shell script tool `populate_reference_data.sh` in the repository root is provided to automatically retrieve and populate this directory with needed and optional datasets from authoritative external sources.

---

## Automated Data Population Utility

You can populate `reference_data/` with all required and optional datasets using the root script:

```bash
# Populate reference_data/ with all default legacy datasets
./populate_reference_data.sh

# Target a specific directory or download newer datasets
./populate_reference_data.sh --target-dir ./reference_data --legacy
./populate_reference_data.sh --etopo2022
./populate_reference_data.sh --all
```

Run `./populate_reference_data.sh --help` for full CLI options and dataset information.

---

## Required & Optional Reference Data Files

### 1. Present / Legacy Datasets (NOAA NCEP Distribution)

* **`etopo1.nc`**
  * **Source**: NOAA National Centers for Environmental Information (NCEI) / NOAA NCEP Server (`ftp://polar.ncep.noaa.gov/waves/gridgen/`)
  * **Size**: ~950 MB
  * **Description**: Global relief model with 1 arc-minute resolution combining global topography and bathymetry.
  * **Usage**: Primary reference bathymetry source used by `gridgen.grid.generate_grid` (Python) and `generate_grid.m` (MATLAB) to interpolate depth/elevation onto target grid coordinates.

* **`etopo2.nc`**
  * **Source**: NOAA NCEI / NOAA NCEP Server (`ftp://polar.ncep.noaa.gov/waves/gridgen/`)
  * **Size**: ~230 MB
  * **Description**: Global relief model with 2 arc-minute resolution combining topography and bathymetry.
  * **Usage**: Secondary reference bathymetry source used when lower resolution grid generation is specified.

* **GSHHS Shoreline Polygon Databases (`coastal_bound_*.mat`)**
  * **GSHHS Version**: Derived from **GSHHS v1.3** (Wessel & Smith, 1996; full resolution containing 188,606 polygons / 180,509 coastal polygons).
  * **Origin & Maintenance**: These `coastal_bound_*.mat` files are **locally maintained MAT-file structures** derived and formatted specifically for WAVEWATCH grid generation pipelines. They are not part of the standard upstream GSHHS/GSHHG distribution (which is published in binary, NetCDF, and Shapefile formats).
  * **Files**:
    * `coastal_bound_full.mat` (~120 MB) - Full resolution (~0.04 km, 188,606 polygons)
    * `coastal_bound_high.mat` (~25 MB) - High resolution (~0.2 km, 153,539 polygons)
    * `coastal_bound_inter.mat` (~7 MB) - Intermediate resolution (~1.0 km, 41,523 polygons)
    * `coastal_bound_low.mat` (~2 MB) - Low resolution (~5.0 km, 10,769 polygons)
    * `coastal_bound_coarse.mat` (~0.5 MB) - Coarse resolution (~25.0 km, 1,866 polygons)
  * **Source**: NOAA NCEP gridgen distribution tarball (`gridgen_addit.tar.gz`).
  * **Usage**: Loaded by grid generation pipelines (`compute_boundary`, `clean_mask`, `split_boundary`, `create_obstr`) to compute domain boundaries, refine land/sea masks, split large shoreline geometries, and calculate subgrid obstruction factors for WAVEWATCH wave modeling.

* **Optional Regional Polygons (`optional_coastal_polygons.mat`)**
  * **Source**: NOAA NCEP gridgen distribution tarball (`gridgen_addit.tar.gz`).
  * **Size**: ~1.5 MB
  * **Description**: Geometry data structures for user-defined optional regional shoreline and coastal feature polygons.
  * **Usage**: Loaded when optional polygon masking (`opt_poly=1`) is enabled.

* **`user_polygons.flag`**
  * **Source**: Version controlled in `reference_data/` of this repository.
  * **Size**: ~1.5 KB
  * **Description**: Plain text configuration file listing numeric identifiers, status toggle flags (`0` = ignore, `1` = include/account for), and regional descriptions for 50 predefined coastal domains (e.g., Hudson Bay, Mediterranean Sea, Chesapeake Bay, San Francisco Harbor).
  * **Usage**: Read by `optional_bound` to determine active optional coastal feature polygons during land/sea mask generation.

---

## Newer Authoritative Reference Datasets

For high-resolution modeling, newer authoritative external datasets are recommended and supported by `populate_reference_data.sh`:

### 1. ETOPO 2022 Global Relief Model (NOAA NCEI)
* **Authoritative Source**: NOAA National Centers for Environmental Information (NCEI)
* **Resolutions Available**: 15 arc-second (~450m), 30 arc-second (~900m), 60 arc-second (~1.8km)
* **Formats**: GeoTIFF (`.tif`) and NetCDF (`.nc`)
* **Description**: Replaces ETOPO1 and ETOPO2 with significantly improved global relief, updated coastal bathymetry, and modern geoid/ice surface options.
* **Retrieval**:
  ```bash
  ./populate_reference_data.sh --etopo2022
  ```
  Or direct download from NOAA NCEI: `https://www.ngdc.noaa.gov/mgg/global/relief/ETOPO2022/data/`

### 2. GEBCO Global Grid (GEBCO 2023 / 2024)
* **Authoritative Source**: General Bathymetric Chart of the Oceans (GEBCO) / IHO-IOC / BODC
* **Resolution**: 15 arc-second global grid
* **Format**: NetCDF-4 (`GEBCO_2024.nc`)
* **Description**: Premier international high-resolution global bathymetric dataset incorporating multibeam survey data and satellite altimetry.
* **Retrieval**:
  ```bash
  ./populate_reference_data.sh --gebco
  ```
  Or direct download: `https://www.gebco.net/data_and_products/gridded_bathymetry_data/`

### 3. GSHHG v2.3.7 Vector Shoreline Database
* **Authoritative Source**: NOAA NCEI / SOEST University of Hawaii
* **Formats**: Binary (`gshhg-bin-2.3.7.zip`), ESRI Shapefile (`gshhg-shp-2.3.7.zip`), NetCDF (`gshhg-nc-2.3.7.zip`)
* **Description**: Latest official release of the Global Self-consistent, Hierarchical, High-resolution Geography database.
* **Retrieval**:
  ```bash
  ./populate_reference_data.sh --gshhg
  ```
