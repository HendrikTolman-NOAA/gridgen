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

This software package has been created for generating grids for WAVEWATCH III using MATLAB. This package has been developed and tested on MATLAB v7 or higher.

## Documentation

Documentation is available at three levels:
1. Grid generation manual: `grid_generation.pdf` (can be found on the wiki page).
2. Comments in the scripts explaining what individual parts of the code are doing.
3. Brief explanations in each subroutine that can be read from the MATLAB workspace by typing `help <name>`, where `<name>` is the subroutine. *(Note: The path to the subroutines should be set when trying this option)*.

## Installation

To create a local clone of the repository:

```bash
git clone https://github.com/NOAA-EMC/gridgen.git
cd gridgen
```

To install the Python package (`ww4gridgen`) and its dependencies in editable mode:

```bash
pip install -e .
```

### Reference Data Population

Large binary reference data files (such as NetCDF bathymetry models and coastal polygon datasets) are excluded from version control and must be placed in the `reference_data/` directory.

To pull in and populate the archive data, run the provided population script:

```bash
./populate_reference_data.sh
```

The script automatically verifies existing datasets in `reference_data/` and will not try to (re-) load or overwrite any file that is already present.

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

## Dependency

MATLAB and NetCDF routines for MATLAB.

NetCDF toolbox for MATLAB can be obtained from [SourceForge](http://mexcdf.sourceforge.net/).

*(Note: NetCDF toolbox is only used for reading global bathymetry data files. If you have your own independent set of routines for reading NetCDF files, then only a few lines need to be changed in the `generate_grid.m` routine. These lines have been marked).*

## Files

There are 3 sub-directories:
- `bin/`: Stores all the scripts used in the grid generation routine.
- `examples/`: Stores 2 examples of master scripts that call the different subroutines for creating grids. An example for a regional grid and a global grid (which has some differences) are shown, as well as a script that is used to modify the traditional land - sea mask for WAVEWATCH III to one for the multi-grid version (version 3.10 and higher). This is done for the regional grid assuming that it would be nested with the global grid in the multi-grid version.
- `reference_data/`: Stores all the reference data needed for creating grids and includes two global grids, GSHHS shoreline polygon database, and an optional user-defined polygon database (combined with a flag file that determines which of these polygons are to be used) for masking out water bodies that do not play a critical role in wave propagation.

## Addendums

1. The `generate_grid` function now has two extra parameters that need to be set before the call can be made — a cut-off depth and a representative depth for dry cells.
2. MATLAB now has built-in support for NetCDF and those have been incorporated in the `generate_grid.m` routine.
3. A series of bugs were cleaned up:
   - Getting rid of spurious `NaN` values in `generate_grid`
   - Changing the algorithm in `compute_boundary` to remove errors associated with improper closing of certain boundaries
   - Speed up in the `clean_mask` routine
   - Generating grids only in the 0 - 360 lon range (this is the range in which the boundaries are defined, and switching to -180 - 180 range was leading to improper treatment of boundary closure in certain cases).

## Important

Gridgen now does not require the grids to be rectilinear to allow for development support for curvilinear grids. Thus lat / lon arrays are now 2-dimensional to allow for varying resolution. Gridgen will not make the arrays needed for the grids. There are a number of software options available for that, but given the grids will generate all other features — bathymetry, masks, and obstruction grids. See examples for how to generate the 2D grids for rectilinear (constant spacing lat/lon) domains.

---

**Last updated:** October 2, 2026

## Disclaimer

The United States Department of Commerce (DOC) GitHub project code is provided on an 'as is' basis and the user assumes responsibility for its use. DOC has relinquished control of the information and no longer has responsibility to protect the integrity, confidentiality, or availability of the information. Any claims against the Department of Commerce stemming from the use of its GitHub project will be governed by all applicable Federal law. Any reference to specific commercial products, processes, or services by service mark, trademark, manufacturer, or otherwise, does not constitute or imply their endorsement, recommendation or favoring by the Department of Commerce. The Department of Commerce seal and logo, or the seal and logo of a DOC bureau, shall not be used in any manner to imply endorsement of any commercial product or activity by DOC or the United States Government.

<p align="right">
  <img src="https://github.com/NOAA-EMC/gridgen/wiki/images/noaa_logo.gif" alt="NOAA Logo" height="50" width="55">
  <img src="https://github.com/NOAA-EMC/gridgen/wiki/images/nws.jpg" alt="NWS Logo" height="50" width="50">
</p>
