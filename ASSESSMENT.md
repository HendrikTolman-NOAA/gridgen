# Assessment: Technology Choice for WW4 Gridgen Migration from MATLAB

**Authors / Contributors:** Jules, Hendrik
**Date:** May 20, 2024

> **Decision Remark (Hendrik):**
> Hendrik selects **Option 2 (Pure Python Architecture)** for the migration. The original MATLAB implementation was not prohibitively slow, and a single-language, pure Python application will be significantly easier to maintain, deploy, and contribute to across the scientific community.

---

## Executive Summary

This document provides a technical assessment for replacing the MATLAB-based WAVEWATCH III (WW3) `gridgen` software package with a modern technology stack for **WW4**.

The new system must support:
1. **NetCDF-UGRID standard format** (conventions for unstructured/structured ocean mesh topologies, face/node connectivity, and metadata).
2. **Zarr chunking & cloud-native storage** (chunked arrays, efficient parallel access, cloud-friendly metadata).
3. **Decoupling from MATLAB** to ensure an open-source, scalable, and maintainable pipeline.

---

## Technical Context & Functional Requirements

The current MATLAB `gridgen` suite performs the following key functions:
1. **Grid Definition & Cell Geometry**: Generating coordinate grids (regular, curvilinear, unstructured) and computing cell corners/widths (`compute_cellcorner.m`).
2. **Bathymetry Averaging & Interpolation**: Reading global DEMs (ETOPO1/ETOPO2/GEBCO) and performing cell-averaging or 4-point bilinear interpolation based on resolution (`generate_grid.m`).
3. **Polygon Masking**: Applying shoreline polygon databases (GSHHG) and user-defined polygons to delineate wet/dry cells and lakes (`clean_mask.m`, `reconcile_masks.m`).
4. **Subgrid Obstructions**: Calculating directional obstruction factors (`create_obstr.m`).
5. **Output Writing**: Exporting grids to ASCII, GMT grid, and traditional NetCDF files (`nc_ww3_grdwrite.m`, `write_ww3file.m`).

For **WW4**, the target output format requires **NetCDF-UGRID** compliance and **Zarr chunked storage capability**.

---

## Detailed Assessment of Options

### Option 1: Pure C++ Architecture

#### **Pros**
- **Maximum Raw Computational Performance**: Direct control over memory allocation, vectorization, and multi-threading (OpenMP/MPI/TBB). Fast execution for high-resolution grid generation.
- **Standalone Binary**: Can be deployed on High-Performance Computing (HPC) clusters as a lightweight standalone executable without a Python runtime dependency.

#### **Cons**
- **Poor NetCDF-UGRID & Zarr Ecosystem**: C++ lacks out-of-the-box, high-level abstractions for UGRID conventions and Zarr stores. Generating NetCDF-UGRID attributes and Zarr datasets requires low-level C API calls or complex third-party library integrations (`libnetcdf`, `HDF5`, custom C++ Zarr writers).
- **High Development & Maintenance Overhead**: Development velocity in C++ for geometric dataset formatting is significantly lower than in high-level scripting languages.
- **Inflexible for Domain Scientists**: Harder for oceanographers and domain experts to customize, script, or integrate into interactive workflows (e.g., Jupyter Notebooks).

---

### Option 2: Pure Python Architecture *(Selected Option)*

#### **Pros**
- **Gold Standard for UGRID & Zarr**: Python is the primary language of the Pangeo stack.
  - **UGRID**: Supported natively via `uxarray` (developed specifically for UGRID-compliant unstructured grids) and `xarray`.
  - **Zarr**: Native support via `zarr-python` and `xarray.to_zarr()`, offering configurable chunking, compression (Blosc, Zstd), and direct cloud export (S3/GCS).
- **Rich Geospatial Ecosystem**: High-performance bindings to C/C++ libraries exist in Python:
  - `shapely` & `geopandas` (built on C++ GEOS) for fast STRtree spatial indexing and polygon clipping.
  - `scipy.spatial` / `scikit-learn` for KDTree and Delaunay triangulation.
  - `rasterio` / `rioxarray` for high-resolution bathymetry DEM raster operations.
- **High Developer Velocity & Single-Language Maintainability**: Easy testing, CI/CD, documentation, interactive user scripting, and easier long-term maintenance as a pure Python package.

#### **Cons**
- **Loop Overhead in Pure Python**: Explicit loops over millions of grid cells or bathymetry points in pure Python can be slow.
- **Solution**: Heavy loops can be easily vectorized with `numpy` or compiled JIT using `numba` without introducing multi-language C++ build complexities.

---

### Option 3: Hybrid Architecture (Python Interface/Driver + C++ / Numba Compute Core)

#### **Pros**
- **Best of Both Worlds**:
  - **Python** handles the high-level orchestration, user CLI/API, dataset schema definition, UGRID metadata formatting, and Zarr/NetCDF I/O export (`xarray` + `uxarray` + `zarr`).
  - **C++ (via `pybind11` / `Cython`) or Numba** handles computational geometry, spatial mesh generation (e.g., CGAL, Triangle, Gmsh bindings), and heavy bathymetry cell-averaging kernels.
- **Modular & Extensible**: Core meshing algorithms can be compiled as shared C++ libraries or Python C-extensions, while keeping user interaction simple and expressive.
- **Performance**: Achieves near-C++ speed for bottleneck algorithms while retaining Python's rich file format and cloud ecosystem.

#### **Cons**
- **Build System Complexity**: Requires managing C++ extension compilation (`scikit-build-core`, `CMake`) across target platforms if standard C++ modules are used.

---

## Performance Analysis: Python vs. MATLAB Execution Speed

### Is Python Expected to Be Faster Than MATLAB?

The short answer is **yes**, an idiomatic scientific Python implementation will be **substantially faster than the existing MATLAB code**, provided the right libraries and paradigms are used.

#### **1. Unoptimized / Naive Python Loops vs. MATLAB JIT**
- If grid generation logic is ported line-by-line using explicit, nested `for` loops in pure Python (e.g., iterating cell-by-cell in `generate_grid.m`), Python will be **slower** than MATLAB. MATLAB includes a built-in JIT compiler that optimizes simple array loops.

#### **2. Idiomatic Scientific Python (Vectorized + Spatial Trees + Numba JIT) vs. MATLAB**
When structured properly using modern Python geospatial tools, Python will outperform MATLAB by **10x to 100x** for the following reasons:

- **Spatial Indexing (`Shapely` / GEOS STRtrees)**:
  - In MATLAB `gridgen`, shoreline masking and lake removal (`clean_mask.m`, `generate_grid.m`) perform brute-force point-in-polygon checks (`inpolygon.m`) across all grid cells for every polygon ($O(N \cdot M)$ complexity).
  - In Python, `shapely` utilizes C-accelerated **GEOS STRtrees (Bounding Volume Hierarchy)**. Querying points against spatial trees reduces complexity to $O(N \log M)$, running orders of magnitude faster.
- **NumPy Vectorization**:
  - Grid corner computations and array operations run directly in compiled C memory blocks.
- **Numba JIT Compilation**:
  - For algorithms requiring explicit element-wise loops (such as bathymetric cell averaging across global DEMs), `@numba.njit` compiles Python directly to native LLVM assembly at runtime, consistently outperforming MATLAB's JIT compiler by **2x to 5x**.
- **Parallelization (`Dask` / `multiprocessing`)**:
  - MATLAB requires Parallel Computing Toolbox licenses and `parfor` setups. Python supports multi-core parallel processing out-of-the-box (`multiprocessing`, `concurrent.futures`, `Dask`), allowing multi-threaded grid generation across all CPU cores without licensing limitations.

---

## Comparison Matrix

| Criteria | C++ | Python (Selected) | Hybrid (Python + C++/Numba) |
| :--- | :--- | :--- | :--- |
| **NetCDF-UGRID Support** | ❌ Poor (Low-level manual formatting) | ✅ Excellent (`uxarray`, `xarray`) | ✅ Excellent (`uxarray`, `xarray`) |
| **Zarr Chunking Support** | ❌ Limited / Immature C++ libraries | ✅ Native (`zarr`, `xarray`, `dask`) | ✅ Native (`zarr`, `xarray`, `dask`) |
| **Computational Geometry** | ✅ Native (CGAL, GEOS, custom C++) | 🟡 Good (`shapely` GEOS bindings) | ✅ Superior (C++ CGAL/GEOS or Numba) |
| **Performance for Large Grids**| ⚡ Fast | 🟡 Moderate (Fast with NumPy/Numba) | ⚡ Fast |
| **Developer Productivity** | ❌ Slow | ✅ Very High | ✅ High |
| **Maintainability for Scientists**| ❌ Low | ✅ High | ✅ High |

---

## Recommended Architecture & Migration Roadmap for WW4

Based on Hendrik's decision, we will adopt a **Pure Python Architecture (Option 2)**.

### **Target Technology Stack**
- **Data Structure & Storage**: `xarray`, `uxarray`, `zarr`, `netCDF4`.
- **Geospatial & Spatial Indexing**: `shapely` (GEOS C-engine with STRtree), `pyproj`, `geopandas`, `scipy.spatial`.
- **Performance Acceleration**: `numpy` vectorization and `@numba.njit` JIT kernels where explicit loops are needed.
- **CLI & Interface**: `click` or `typer` for command-line grid generation scripts.

### **Phased Migration Plan**

1. **Phase 1: Python UGRID & Zarr Core Pipeline**
   - Create Python package structure (`ww4-gridgen`).
   - Define UGRID 1.0 schema generation routines using `xarray`/`uxarray`.
   - Implement Zarr export with configurable chunking (e.g., spatial chunking `(face: 10000)` or `(y: 256, x: 256)`).

2. **Phase 2: Bathymetry & Masking Algorithms**
   - Port `generate_grid.m` and `compute_cellcorner.m` to Python using NumPy vectorization and Shapely spatial trees (`STRtree`) for rapid point-in-polygon queries.
   - Use `numba` JIT functions for cell-averaging loops over dense global DEMs (ETOPO/GEBCO).

3. **Phase 3: Subgrid Obstructions & Boundary Processing**
   - Port subgrid obstruction and boundary reconciliation functions (`create_obstr.m`, `reconcile_masks.m`).

4. **Phase 4: Validation & Benchmark**
   - Validate generated WW4 UGRID Zarr datasets against existing MATLAB grid output for accuracy and performance benchmarking.

---

## Conclusion

A **Pure Python Architecture (Option 2)** is selected as the target for WW4 grid generation. It directly solves the requirement for NetCDF-UGRID compliance and Zarr chunking via mature Python Pangeo libraries, achieves high performance through vectorization and Numba/GEOS C-bindings, and ensures maximum maintainability as a single-codebase application.
