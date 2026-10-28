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
# @date Latest Update: 2026-10-28

"""Unit tests for defining input boundary points in regional grids."""

from __future__ import annotations

import numpy as np

from gridgen.coordinates import create_regular_grid
from gridgen.masking import define_boundary_points, modify_mask


def test_define_boundary_points_edges() -> None:
    """Test setting outer domain boundary wet cells to mask value 2."""
    lon, lat = create_regular_grid(
        LON_START=0, LON_END=4, LAT_START=0, LAT_END=4, NX=5, NY=5
    )
    mask = np.ones((5, 5), dtype=int)
    # Set one cell to dry land
    mask[0, 0] = 0

    m_new = define_boundary_points(mask, lon, lat)

    # Dry land remains 0
    assert m_new[0, 0] == 0
    # Outer wet cells set to 2
    assert m_new[0, 1] == 2
    assert m_new[4, 4] == 2
    # Inner wet cells remain 1
    assert m_new[2, 2] == 1


def test_define_boundary_points_active_poly() -> None:
    """Test defining active computation polygon region and internal boundaries."""
    lon, lat = create_regular_grid(
        LON_START=0, LON_END=10, LAT_START=0, LAT_END=10, NX=11, NY=11
    )
    mask = np.ones((11, 11), dtype=int)

    # Active polygon covering center (2,2) to (8,8)
    px = np.array([2.0, 8.0, 8.0, 2.0, 2.0])
    py = np.array([2.0, 2.0, 8.0, 8.0, 2.0])

    m_new = define_boundary_points(mask, lon, lat, active_poly=(px, py))

    # Center cell is active wet (1)
    assert m_new[5, 5] == 1
    # Outside cell (0, 0) is inactive (3)
    assert m_new[0, 0] == 3


def test_modify_mask_alias() -> None:
    """Test modify_mask backward compatibility alias."""
    lon, lat = create_regular_grid(
        LON_START=0, LON_END=4, LAT_START=0, LAT_END=4, NX=5, NY=5
    )
    mask = np.ones((5, 5), dtype=int)

    m_new = modify_mask(mask, lon, lat)
    assert m_new[0, 1] == 2


def test_define_boundary_points_count(capsys) -> None:
    """Test counting and reporting boundary points generated."""
    lon, lat = create_regular_grid(
        LON_START=0, LON_END=4, LAT_START=0, LAT_END=4, NX=5, NY=5
    )
    mask = np.ones((5, 5), dtype=int)

    m_new = define_boundary_points(mask, lon, lat)
    num_bnd = np.count_nonzero(m_new == 2)
    assert num_bnd == 16  # 5x5 outer boundary wet cells (4*5 - 4)

    captured = capsys.readouterr()
    assert "Generated 16 input boundary points" in captured.out


def test_define_boundary_points_range() -> None:
    """Test restricting boundary points to allowed latitude and longitude range."""
    lon, lat = create_regular_grid(
        LON_START=0, LON_END=4, LAT_START=0, LAT_END=4, NX=5, NY=5
    )
    mask = np.ones((5, 5), dtype=int)

    # Restrict boundary points to lon in [0.0, 2.0] and lat in [0.0, 4.0]
    m_new = define_boundary_points(mask, lon, lat, bound_range=(0.0, 2.0, 0.0, 4.0))

    # Boundary cells with lon <= 2.0 are kept as 2
    assert m_new[0, 0] == 2
    assert m_new[0, 1] == 2
    assert m_new[0, 2] == 2

    # Boundary cells with lon > 2.0 revert to wet 1
    assert m_new[0, 3] == 1
    assert m_new[0, 4] == 1
    assert m_new[2, 4] == 1


def test_cli_boundary_points_optional_range(tmp_path) -> None:
    """Test gridgen.cli --boundary-points with 0 arguments vs 4 range arguments."""
    import subprocess
    from pathlib import Path

    repo_root = Path(__file__).parent.parent
    script_path = repo_root / "run_gridgen.sh"

    # 1. Execute run_gridgen.sh with --boundary-points without range arguments
    out_nc1 = tmp_path / "bnd_no_range_ugrid.nc"
    res1 = subprocess.run(
        [
            str(script_path),
            "-n",
            "bnd_no_range",
            "--nx",
            "10",
            "--ny",
            "10",
            "--lon-start",
            "-70",
            "--lat-start",
            "20",
            "--lon-end",
            "-60",
            "--lat-end",
            "30",
            "-o",
            str(tmp_path),
            "--boundary-points",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert res1.returncode == 0
    assert "Boundary points generated: 36 (mask value 2)." in res1.stdout
    assert out_nc1.exists()

    # 2. Execute run_gridgen.sh with --boundary-points and 4 range arguments
    out_nc2 = tmp_path / "bnd_range_ugrid.nc"
    res2 = subprocess.run(
        [
            str(script_path),
            "-n",
            "bnd_range",
            "--nx",
            "10",
            "--ny",
            "10",
            "--lon-start",
            "-70",
            "--lat-start",
            "20",
            "--lon-end",
            "-60",
            "--lat-end",
            "30",
            "-o",
            str(tmp_path),
            "--boundary-points",
            "-70",
            "-65",
            "20",
            "30",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert res2.returncode == 0
    assert "Boundary points generated: 18 (mask value 2)." in res2.stdout
    assert out_nc2.exists()
