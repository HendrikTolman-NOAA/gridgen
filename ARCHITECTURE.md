# WAVEWATCH III (WW3) / WAVEWATCH IV (WW4) Gridgen Architecture

This document describes the workflow, data processing steps, and module architecture for the WAVEWATCH III / IV Python Grid Generation Package (`ww4gridgen`).

## Workflow Overview

The grid generation package converts high-resolution source bathymetry and shoreline datasets into structured grid representations used by WAVEWATCH III and WAVEWATCH IV.

### 1. Software & Model Environment Setup

```mermaid
flowchart TD
    subgraph Init Step 1: Software Acquisition & Environment Setup
        A0[GitHub Repository<br/>NOAA-EMC/gridgen] --> A1[git clone https://github.com/NOAA-EMC/gridgen.git]
        A1 --> A2[Verify Python Packages<br/>numpy, scipy, xarray, netCDF4, zarr, shapely, matplotlib]
    end

    subgraph Init Step 2: Reference Data Population
        B[populate_reference_data.sh]
        B --> C1[Download / Extract Legacy Datasets<br/>etopo1.nc, etopo2.nc, coastal_bound_*.mat]
        B --> C2[Download ETOPO 2022<br/>ETOPO_2022_v1_60s_N90W180_bed.tif]
        C1 --> D[(reference_data/ Directory)]
        C2 --> D
    end

    A2 --> B
```

### 2. Tool Execution & Grid Generation Pipeline

```mermaid
flowchart TD
    subgraph Run Step 1: Driver Execution & Validation
        E[User CLI / Script Call] --> F[run_gridgen.sh]
        F --> G{Check reference_data/}
        G -- Missing / Empty --> H[Error & Stop:<br/>Prompt user to run populate_reference_data.sh]
        G -- Datasets Present --> I[Invoke Python CLI:<br/>python3 -m gridgen.cli]
    end

    subgraph Run Step 2: Core Grid Processing Pipeline
        I --> J[gridgen.grid.generate_grid]
        J --> K{Check Bathymetry File}
        K -- File Missing --> L[Raise FileNotFoundError & Stop]
        K -- File Found --> M[Interpolate & Average Bathymetry<br/>Cell corners & polygon overlap]

        M --> N[gridgen.masking.remove_lake]
        N --> O[Generate Land/Sea Mask]

        O --> P[gridgen.obstructions.create_obstr]
        P --> Q[Calculate Grid Obstructions sx, sy]
    end

    subgraph Run Step 3: Multi-Format Export & Visualization
        Q --> R1[gridgen.io.ascii<br/>Legacy WW3 ASCII<br/>.depth_ascii, .maskorig_ascii, .obstr_lev1, .meta]
        Q --> R2[gridgen.io.coards<br/>Legacy GMT COARDS NetCDF<br/>_coards.nc]
        Q --> R3[gridgen.io.ugrid<br/>WW4 NetCDF-UGRID 1.0<br/>_ugrid.nc]
        Q --> R4[gridgen.io.zarr_store<br/>WW4 Zarr Store<br/>_ugrid.zarr]
        Q --> R5[plot_grid.sh / gridgen.vis<br/>Graphical Plots<br/>.jpg, .png, .pdf, .eps, .gif]
        R5 --> R6[view_grid.sh<br/>Display Graphics Window]
    end
```

## Step-by-Step Processing Pipeline

### Model Setup Stage

- **Init Step 1: Software Acquisition & Environment Verification (`git clone` & Package Check)**
  - Obtain the software package by cloning the repository from GitHub (`https://github.com/NOAA-EMC/gridgen.git`), setting up the Python environment and search path, and verifying required Python dependencies (`numpy`, `scipy`, `xarray`, `netCDF4`, `zarr`, `shapely`, `matplotlib`).

- **Init Step 2: Reference Data Population (`populate_reference_data.sh`)**
  - Populates bathymetry grids (`etopo1.nc`, `etopo2.nc`, or ETOPO 2022) and shoreline boundary MAT files (`coastal_bound_*.mat`) in `reference_data/`.

### Tool Execution Stage

- **Run Step 1: Driver Check & Execution (`run_gridgen.sh` & `gridgen.cli`)**
  - Verifies Python dependency availability (`numpy`, `scipy`, `xarray`, `netCDF4`, `zarr`, `shapely`, `matplotlib`).
  - Ensures `reference_data/` contains bathymetry datasets before invoking `python3 -m gridgen.cli`.

- **Run Step 2: Core Grid Processing Pipeline (`gridgen.grid`, `gridgen.masking`, `gridgen.obstructions`)**
  - **Bathymetry Extraction:** Computes target grid cell corner polygons (`compute_cellcorner`), extracts/averages sub-grid base bathymetry depths or performs bilinear interpolation, and assigns dry values (`999999.0`) to cells above cut-off depth.
  - **Masking & Lake Removal:** Constructs initial binary land/sea mask based on depth values, cleans disconnected water bodies, and applies lake tolerance rules (`remove_lake`).
  - **Sub-grid Obstruction Calculation:** Intersects cell boundary faces with shoreline polygons to produce directional sub-grid obstruction factors `sx` and `sy` (`create_obstr`).

- **Run Step 3: Multi-Format Grid Export (`gridgen.io.*`)**
  - **Legacy WW3 ASCII:** `.depth_ascii`, `.maskorig_ascii`, `.obstr_lev1`, `.meta`
  - **Legacy GMT/NetCDF COARDS:** `_coards.nc`
  - **WW4 NetCDF-UGRID 1.0:** `_ugrid.nc`
  - **WW4 Zarr Store:** `_ugrid.zarr`

- **Run Step 4: Graphical Display & Visualization (`plot_grid.sh` / `gridgen.vis` / `view_grid.sh`)**
  - Generates multi-panel plot graphics displaying bathymetry depth, land-sea masks, and sub-grid directional obstruction factors (`sx`, `sy`) in `jpg`, `png`, `pdf`, `eps`, or `gif` formats, and displays generated graphics in the present window (`view_grid.sh`).
