# WAVEWATCH III (WW3) / WAVEWATCH IV (WW4) Gridgen Package Tests
#
# Copyright 2026 National Weather Service (NWS), NOAA. All rights reserved.
# NWS often uses Generative AI (GenAI) for code development and refactoring.
# Whenever GenAI is used, NWS requires a full human review of code before it
# is added to its repositories.
#
# @author Aldgisl (Agentic AI), Hendrik Tolman
# @date Initial: 2026-09-22

from __future__ import annotations

import numpy as np

from gridgen.geometry import compute_all_corners, compute_cellcorner


def test_compute_cellcorner_simple():
    lon1d = np.array([10.0, 11.0, 12.0])
    lat1d = np.array([20.0, 21.0, 22.0])
    lon, lat = np.meshgrid(lon1d, lat1d)

    c1, c2, c3, c4, wdth, hgt = compute_cellcorner(lon, lat, j=1, k=1)

    assert c1.shape == (2,)
    assert c2.shape == (2,)
    assert c3.shape == (2,)
    assert c4.shape == (2,)
    assert wdth > 0
    assert hgt > 0


def test_compute_all_corners():
    lon1d = np.array([10.0, 11.0, 12.0])
    lat1d = np.array([20.0, 21.0, 22.0])
    lon, lat = np.meshgrid(lon1d, lat1d)

    polygons, widths, heights = compute_all_corners(lon, lat)

    assert polygons.shape == (3, 3, 5, 2)
    assert widths.shape == (3, 3)
    assert heights.shape == (3, 3)
