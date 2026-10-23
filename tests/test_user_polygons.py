# WAVEWATCH III (WW3) / WAVEWATCH IV (WW4) Gridgen Package
#
# Copyright 2026 National Weather Service (NWS), NOAA. All rights reserved.
# NWS often uses Generative AI (GenAI) for code development and refactoring.
# Whenever GenAI is used, NWS requires a full human review of code before it
# is added to its repositories.
#
# @author Aldgisl (Agentic AI), Hendrik Tolman
# @author Jules (Agentic AI) (contributor)
# @date Initial: 2026-10-06
# @date Latest Update: 2026-10-23

"""Unit tests for user-defined optional coastal polygon loading."""

from __future__ import annotations

import os

import numpy as np
import scipy.io as sio

from gridgen.coordinates import create_regular_grid
from gridgen.masking import clean_mask, load_user_polygons


class DummyBound:
    """Dummy struct class for MAT user_bound objects."""

    def __init__(self, x: np.ndarray, y: np.ndarray, level: int = 1) -> None:
        self.x = x
        self.y = y
        self.level = level


def test_load_user_polygons_txt(tmp_path) -> None:
    """Test loading optional user coastal polygons from plain text format with flag file switches."""
    ref_dir = str(tmp_path)
    txt_filename = "optional_coastal_polygons.txt"
    txt_path = os.path.join(ref_dir, txt_filename)

    # Write dummy plain text polygons file
    with open(txt_path, "w") as f:
        f.write("# Polygon 1: Test Poly 1 (Level: 1, Points: 5)\n")
        f.write("10.0 10.0\n20.0 10.0\n20.0 20.0\n10.0 20.0\n10.0 10.0\n\n")
        f.write("# Polygon 2: Test Poly 2 (Level: 1, Points: 5)\n")
        f.write("30.0 30.0\n40.0 30.0\n40.0 40.0\n30.0 40.0\n30.0 30.0\n\n")

    # Create flag file enabling only polygon 2 (0 then 1)
    flag_path = os.path.join(ref_dir, "user_polygons.flag")
    with open(flag_path, "w") as f:
        f.write("1 0\n")
        f.write("2 1\n")

    active_polys = load_user_polygons(
        ref_dir=ref_dir, flag_file=flag_path, txt_filename=txt_filename
    )

    assert len(active_polys) == 1
    assert np.isclose(active_polys[0]["west"], 30.0)
    assert np.isclose(active_polys[0]["east"], 40.0)


def test_load_repo_gridgen_data() -> None:
    """Test loading actual repository gridgen_data files with default parameters."""
    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    gridgen_data_dir = os.path.join(repo_root, "gridgen_data")

    active_polys = load_user_polygons(ref_dir=gridgen_data_dir)
    assert isinstance(active_polys, list)
    # user_polygons.flag has active polygons (e.g. Black Sea and Baltic Sea set to 1)
    assert len(active_polys) == 2

    txt_file = os.path.join(gridgen_data_dir, "optional_coastal_polygons.txt")
    assert os.path.exists(txt_file)
    mat_file = os.path.join(gridgen_data_dir, "optional_coastal_polygons.mat")
    assert not os.path.exists(mat_file)


def test_load_user_polygons_mat_fallback(tmp_path) -> None:
    """Test MAT polygon file fallback when text file is absent."""
    ref_dir = str(tmp_path)
    mat_filename = "optional_coastal_polygons.mat"
    mat_path = os.path.join(ref_dir, mat_filename)

    poly1 = DummyBound(
        np.array([10.0, 20.0, 20.0, 10.0, 10.0]),
        np.array([10.0, 10.0, 20.0, 20.0, 10.0]),
    )
    sio.savemat(mat_path, {"user_bound": np.array([poly1], dtype=object)})

    flag_path = os.path.join(ref_dir, "user_polygons.flag")
    with open(flag_path, "w") as f:
        f.write("1 1\n")

    active_polys = load_user_polygons(
        ref_dir=ref_dir, flag_file=flag_path, mat_filename=mat_filename
    )
    assert len(active_polys) == 1
    assert np.isclose(active_polys[0]["west"], 10.0)


def test_clean_mask_global_closure() -> None:
    """Test polygon masking properly addresses 360-degree longitude wrap-around on global grid."""
    lon, lat = create_regular_grid(
        NX=36,
        NY=18,
        LON_START=0.0,
        LON_END=350.0,
        LAT_START=-80.0,
        LAT_END=80.0,
    )
    mask = np.ones_like(lon, dtype=int)

    # Polygon at negative longitudes [-10, 10]
    poly_neg = {
        "x": np.array([-10.0, 10.0, 10.0, -10.0, -10.0]),
        "y": np.array([-10.0, -10.0, 10.0, 10.0, -10.0]),
        "level": 1,
    }

    # Apply clean_mask on global grid (longitudes 0..350)
    cleaned = clean_mask(lon, lat, mask, [poly_neg])

    # Check that cells in [0, 10] AND cells in [350, 360] (350 = -10 mod 360) are masked dry (0)
    idx_start = np.where((lon >= 0.0) & (lon <= 10.0) & (lat >= -10.0) & (lat <= 10.0))
    idx_end = np.where((lon >= 350.0) & (lat >= -10.0) & (lat <= 10.0))

    assert np.all(cleaned[idx_start] == 0)
    assert np.all(cleaned[idx_end] == 0)
