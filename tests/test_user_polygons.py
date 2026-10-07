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
# @date Latest Update: 2026-10-07

"""Unit tests for user-defined optional coastal polygon loading."""

from __future__ import annotations

import os

import numpy as np
import scipy.io as sio

from gridgen.masking import load_user_polygons


class DummyBound:
    """Dummy struct class for MAT user_bound objects."""

    def __init__(self, x: np.ndarray, y: np.ndarray, level: int = 1) -> None:
        self.x = x
        self.y = y
        self.level = level


def test_load_user_polygons(tmp_path) -> None:
    """Test loading optional user coastal polygons with flag file switches."""
    ref_dir = str(tmp_path)
    mat_filename = "optional_coastal_polygons.mat"
    mat_path = os.path.join(ref_dir, mat_filename)

    # Create dummy user_bound array
    poly1 = DummyBound(np.array([10.0, 20.0, 20.0, 10.0, 10.0]), np.array([10.0, 10.0, 20.0, 20.0, 10.0]))
    poly2 = DummyBound(np.array([30.0, 40.0, 40.0, 30.0, 30.0]), np.array([30.0, 30.0, 40.0, 40.0, 30.0]))

    sio.savemat(mat_path, {"user_bound": np.array([poly1, poly2], dtype=object)})

    # Create flag file enabling only polygon 2 (0 then 1)
    flag_path = os.path.join(ref_dir, "user_polygons.flag")
    with open(flag_path, "w") as f:
        f.write("1 0\n")
        f.write("2 1\n")

    active_polys = load_user_polygons(ref_dir=ref_dir, flag_file=flag_path, mat_filename=mat_filename)

    assert len(active_polys) == 1
    assert np.isclose(active_polys[0]["west"], 30.0)
    assert np.isclose(active_polys[0]["east"], 40.0)
