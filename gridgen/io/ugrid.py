# WAVEWATCH IV (WW4) Gridgen Package
#
# Copyright 2026 National Weather Service (NWS), NOAA. All rights reserved.
# NWS often uses Generative AI (GenAI) for code development and refactoring.
# Whenever GenAI is used, NWS requires a full human review of code before it
# is added to its repositories.
#
# @author Aldgisl (Agentic AI)
# @author Hendrik Tolman
# @date Initial: 2026-05-20
# @date Update: 2026-05-20
#
# Code Heritage:
# WAVEWATCH IV NetCDF-UGRID 1.0 format exporter module.

"""NetCDF-UGRID 1.0 dataset generator and writer for WAVEWATCH IV."""

from __future__ import annotations

from datetime import datetime, timezone

import numpy as np
import xarray as xr

from ..geometry import compute_all_corners


def create_ugrid_dataset(
    x: np.ndarray,
    y: np.ndarray,
    depth: np.ndarray,
    mask: np.ndarray,
    sx: np.ndarray | None = None,
    sy: np.ndarray | None = None,
    title: str = "WAVEWATCH IV UGRID Mesh",
    start_index: int = 0,
) -> xr.Dataset:
    """Create an xarray Dataset compliant with the NetCDF-UGRID 1.0 conventions.

    Parameters
    ----------
    x : np.ndarray
        2D longitude array of shape (Ny, Nx).
    y : np.ndarray
        2D latitude array of shape (Ny, Nx).
    depth : np.ndarray
        2D bathymetry depth array of shape (Ny, Nx).
    mask : np.ndarray
        2D land/sea mask array of shape (Ny, Nx).
    sx : Optional[np.ndarray]
        2D subgrid x-obstruction array of shape (Ny, Nx).
    sy : Optional[np.ndarray]
        2D subgrid y-obstruction array of shape (Ny, Nx).
    title : str
        Dataset title attribute.
    start_index : int
        0 or 1 index base for face_node_connectivity.

    Returns
    -------
    ds : xr.Dataset
        NetCDF-UGRID 1.0 compliant xarray Dataset.
    """
    Ny, Nx = x.shape
    num_faces = Ny * Nx

    polygons, _, _ = compute_all_corners(x, y)

    # Calculate grid node mesh (Ny+1, Nx+1)
    nodes = {}
    node_coords = []
    connectivity = np.zeros((num_faces, 4), dtype=int)

    for k in range(Ny):
        for j in range(Nx):
            face_idx = k * Nx + j
            cell_corners = polygons[k, j, :4]  # c4, c1, c2, c3

            face_node_indices = []
            for corner in cell_corners:
                key = (round(float(corner[0]), 6), round(float(corner[1]), 6))
                if key not in nodes:
                    nodes[key] = len(node_coords)
                    node_coords.append(corner)
                face_node_indices.append(nodes[key] + start_index)

            connectivity[face_idx, :] = face_node_indices

    node_coords_arr = np.array(node_coords, dtype=np.float64)
    node_lon = node_coords_arr[:, 0]
    node_lat = node_coords_arr[:, 1]

    face_lon = x.ravel()
    face_lat = y.ravel()
    face_depth = depth.ravel()
    face_mask = mask.ravel()

    data_vars = {
        "mesh_topology": (
            (),
            0,
            {
                "cf_role": "mesh_topology",
                "topology_dimension": 2,
                "node_coordinates": "node_lon node_lat",
                "face_coordinates": "face_lon face_lat",
                "face_node_connectivity": "face_node_connectivity",
                "face_dimension": "nMesh2_face",
            },
        ),
        "face_node_connectivity": (
            ("nMesh2_face", "nMaxMesh2_face_nodes"),
            connectivity,
            {
                "cf_role": "face_node_connectivity",
                "start_index": start_index,
                "long_name": "Maps every face cell to its corner node indices",
            },
        ),
        "depth": (
            ("nMesh2_face",),
            face_depth.astype(np.float32),
            {
                "long_name": "Bathymetry depth",
                "standard_name": "sea_floor_depth_below_sea_surface",
                "units": "m",
                "mesh": "mesh_topology",
                "location": "face",
                "coordinates": "face_lon face_lat",
            },
        ),
        "mask": (
            ("nMesh2_face",),
            face_mask.astype(np.int32),
            {
                "long_name": "Land sea mask",
                "units": "1",
                "mesh": "mesh_topology",
                "location": "face",
                "coordinates": "face_lon face_lat",
                "flag_values": [0, 1],
                "flag_meanings": "dry wet",
            },
        ),
    }

    if sx is not None:
        data_vars["sx"] = (
            ("nMesh2_face",),
            sx.ravel().astype(np.float32),
            {
                "long_name": "Subgrid obstruction factor in x direction",
                "units": "1",
                "mesh": "mesh_topology",
                "location": "face",
                "coordinates": "face_lon face_lat",
            },
        )

    if sy is not None:
        data_vars["sy"] = (
            ("nMesh2_face",),
            sy.ravel().astype(np.float32),
            {
                "long_name": "Subgrid obstruction factor in y direction",
                "units": "1",
                "mesh": "mesh_topology",
                "location": "face",
                "coordinates": "face_lon face_lat",
            },
        )

    ds = xr.Dataset(
        data_vars=data_vars,
        coords={
            "node_lon": (
                ("nMesh2_node",),
                node_lon.astype(np.float64),
                {
                    "standard_name": "longitude",
                    "long_name": "Longitude of mesh nodes",
                    "units": "degrees_east",
                },
            ),
            "node_lat": (
                ("nMesh2_node",),
                node_lat.astype(np.float64),
                {
                    "standard_name": "latitude",
                    "long_name": "Latitude of mesh nodes",
                    "units": "degrees_north",
                },
            ),
            "face_lon": (
                ("nMesh2_face",),
                face_lon.astype(np.float64),
                {
                    "standard_name": "longitude",
                    "long_name": "Longitude of face centers",
                    "units": "degrees_east",
                },
            ),
            "face_lat": (
                ("nMesh2_face",),
                face_lat.astype(np.float64),
                {
                    "standard_name": "latitude",
                    "long_name": "Latitude of face centers",
                    "units": "degrees_north",
                },
            ),
        },
        attrs={
            "Conventions": "CF-1.8 UGRID-1.0",
            "title": title,
            "source": "WAVEWATCH IV Gridgen Package",
            "history": f"Created {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')}",
        },
    )

    return ds


def write_ugrid_nc(ds: xr.Dataset, filename: str) -> None:
    """Write UGRID xarray Dataset to NetCDF file.

    Parameters
    ----------
    ds : xr.Dataset
        NetCDF-UGRID compliant xarray Dataset.
    filename : str
        Target output NetCDF file path.
    """
    ds.to_netcdf(filename)
