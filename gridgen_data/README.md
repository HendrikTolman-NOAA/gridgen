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
# @date Initial: 2026-10-22
# @date Latest Update: 2026-10-22
-->

<p align="center">
  <img src="https://github.com/NOAA-EMC/gridgen/wiki/images/WW_tools_banner.jpg" alt="WW_tools_banner" height="100">
</p>

# WAVEWATCH III (WW3) / WAVEWATCH IV (WW4) Gridgen Data Directory

This directory (`gridgen_data/`) contains internal polygon configuration datasets unique to the `ww4gridgen` tool. Unlike large external bathymetry grids and shoreline vector databases stored in `reference_data/`, the files in this directory are lightweight, tool-specific assets that are maintained directly within version control.

---

## Files in this Directory

### 1. Polygon Switch Control File (`user_polygons.flag`)
* **Format**: Plain text (`.flag`)
* **Description**: Contains binary toggle flags (`0` = ignore, `1` = include/mask) and regional name descriptions for 50 predefined coastal feature polygons (e.g., Hudson Bay, Mediterranean Sea, Chesapeake Bay, San Francisco Harbor).
* **Usage**: Read by `gridgen.masking.load_user_polygons` to determine which user-defined optional coastal polygons should be active during land/sea mask cleaning (`clean_mask`) and subgrid obstruction generation (`create_obstr`).

### 2. Polygon Coordinate Database (`optional_coastal_polygons.mat`)
* **Format**: MATLAB MAT-file (`.mat`)
* **Description**: Structured array (`user_bound`) storing coordinate polygon boundaries (`x`, `y` coordinates and nesting levels) for the 50 user-defined optional regional coastal domains.
* **Usage**: Loaded by `gridgen.masking.load_user_polygons` when user-defined optional polygon masking is enabled via `--user-polygons-flag`.

---

## Command Line Usage

When invoking grid generation, the polygon database files in `gridgen_data/` are automatically loaded by default when `--user-polygons-flag` is specified:

```bash
# Enable user coastal polygon masking with default switch control file
./run_gridgen.sh --user-polygons-flag gridgen_data/user_polygons.flag

# Or run directly via Python CLI
python3 -m gridgen.cli --user-polygons-flag gridgen_data/user_polygons.flag
```

Custom flag control files or polygon database directories can be provided via `--user-polygons-flag FILE` and `--gridgen-data-dir DIR`.

---

<p align="right">
  <img src="https://github.com/NOAA-EMC/gridgen/wiki/images/noaa_logo.gif" alt="NOAA Logo" height="50" width="55">
  <img src="https://github.com/NOAA-EMC/gridgen/wiki/images/nws.jpg" alt="NWS Logo" height="50" width="50">
</p>
