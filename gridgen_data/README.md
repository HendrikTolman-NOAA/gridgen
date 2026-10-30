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
# @date Latest Update: 2026-10-23
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
* **Description**: Contains binary toggle flags (`0` = ignore, `1` = include/mask) and regional name descriptions for 100 predefined coastal feature polygons (e.g., Caspian Sea, Netherlands below sea level IJsselmeer, Markermeer, Noord/Zuid Holland, Utrecht, Aegean Sea, Adriatic, Sea of Azov, Gulf of Riga and Moonsund, Baltic Sea - Gulf of Gdansk, Baltic Sea - Kurisches Haff, Baltic Sea - Bay of Greifswald and waters around Rugen, Aland Islands and Turku Archipelago, Denmark inner seas, Denmark - Oresund, Wester Schelde, Waddenzee East/North of Elbe River, Norway: Oslofjord, Norway: Hardangerfjord, Norway: Sognefjord, Norway: Trondheimsfjord, Norway: Vestfjorden, Norway: Varangerfjorden, Norway: Northern Fjords, UK: Firth of Forth, UK: Moray Firth, UK: Solway Firth, UK: The Wash, UK: Thames Estuary, UK: Bristol Channel, UK: Irish Sea, UK: Orkney Islands, UK: Shetland Islands, UK: Hebrides, UK: Inner Hebrides, Firth of Clyde, and SW Islands, Faroe Islands, Hudson Bay, Mediterranean Sea, Chesapeake Bay, Japan: Uchiura Bay, Japan: Mutsu Bay, Japan: Tokyo Bay, Japan: Seto Inland Sea, Japan: Yamaguchi Bay, San Francisco Harbor).
* **Usage**: Read by `gridgen.masking.load_user_polygons` to determine which user-defined optional coastal polygons should be active during land/sea mask cleaning (`clean_mask`) and subgrid obstruction generation (`create_obstr`).

### 2. Polygon Coordinate Database (`optional_coastal_polygons.txt`)
* **Format**: Plain text (`.txt`)
* **Description**: Plain text database storing coordinate polygon boundaries (`x`, `y` coordinates and nesting levels) for the 100 user-defined optional regional coastal domains.
* **Usage**: Loaded by `gridgen.masking.load_user_polygons` during land/sea mask cleaning (`clean_mask`) and subgrid obstruction factor generation (`create_obstr`).

---

## Command Line Usage

When invoking grid generation, the polygon database files in `gridgen_data/` are automatically loaded by default:

```bash
# Run grid generation with default user polygon masking from gridgen_data/
./run_gridgen.sh

# Or run directly via Python CLI
python3 -m gridgen.cli

# Use local directory (.) polygon files instead of gridgen_data/
./run_gridgen.sh --local-polygons

# Disable user coastal polygon masking completely
./run_gridgen.sh --no-user-polygons

# Apply all coastal polygons independent of switch flag values
./run_gridgen.sh --all-polygons
```

---

<p align="right">
  <img src="https://github.com/NOAA-EMC/gridgen/wiki/images/noaa_logo.gif" alt="NOAA Logo" height="50" width="55">
  <img src="https://github.com/NOAA-EMC/gridgen/wiki/images/nws.jpg" alt="NWS Logo" height="50" width="50">
</p>
