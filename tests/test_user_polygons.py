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
# @date Latest Update: 2026-10-20

"""Unit tests for user-defined optional coastal polygon loading."""

from __future__ import annotations

import os
import subprocess
import sys

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
        ref_dir=ref_dir, flag_file=flag_path
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
    # user_polygons.flag has 62 active polygons set to 1 out of 77 total
    assert len(active_polys) == 62

    txt_file = os.path.join(gridgen_data_dir, "optional_coastal_polygons.txt")
    assert os.path.exists(txt_file)
    mat_file = os.path.join(gridgen_data_dir, "optional_coastal_polygons.mat")
    assert not os.path.exists(mat_file)


def test_strict_polygon_filename_requirement(tmp_path) -> None:
    """Test that load_user_polygons strictly requires optional_coastal_polygons.txt and disallows alternate file names/formats."""
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

    # .mat file should not be loaded
    active_polys = load_user_polygons(ref_dir=ref_dir, flag_file=flag_path)
    # Ensure none of the loaded polygons come from the .mat file (which had west == 10.0)
    for p in active_polys:
        assert not np.isclose(p["west"], 10.0)


def test_custom_user_polygons_flag(tmp_path) -> None:
    """Test loading user polygons with a custom user-defined flag file name."""
    ref_dir = str(tmp_path)
    txt_path = os.path.join(ref_dir, "optional_coastal_polygons.txt")
    with open(txt_path, "w") as f:
        f.write("# Polygon 1: Test Poly 1 (Level: 1, Points: 5)\n")
        f.write("0.0 0.0\n10.0 0.0\n10.0 10.0\n0.0 10.0\n0.0 0.0\n\n")
        f.write("# Polygon 2: Test Poly 2 (Level: 1, Points: 5)\n")
        f.write("20.0 20.0\n30.0 20.0\n30.0 30.0\n20.0 30.0\n20.0 20.0\n\n")

    custom_flag_path = os.path.join(ref_dir, "my_custom.flag")
    with open(custom_flag_path, "w") as f:
        f.write("1 0\n2 1\n")

    active_polys = load_user_polygons(ref_dir=ref_dir, flag_file="my_custom.flag")
    assert len(active_polys) == 1
    assert np.isclose(active_polys[0]["west"], 20.0)


def test_obstruction_progress_counter(capsys) -> None:
    """Test that create_obstr writes a progress counter to stdout."""
    from gridgen.obstructions import create_obstr

    x, y = create_regular_grid(
        NX=5, NY=5, LON_START=0.0, LON_END=4.0, LAT_START=0.0, LAT_END=4.0
    )
    mask = np.ones_like(x, dtype=int)
    poly = {
        "x": np.array([1.0, 3.0, 3.0, 1.0, 1.0]),
        "y": np.array([1.0, 1.0, 3.0, 3.0, 1.0]),
        "level": 1,
    }

    _ObsX, _ObsY = create_obstr(x, y, [poly], mask)
    captured = capsys.readouterr()
    assert "Calculating subgrid obstructions..." in captured.out


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


def test_cli_automatic_user_polygons_and_local_flags(tmp_path) -> None:
    """Test gridgen CLI automatic polygon loading by default, --local-polygons, and --no-user-polygons."""
    # Setup dummy reference bathymetry dataset
    ref_dir = tmp_path / "ref_data"
    ref_dir.mkdir(parents=True, exist_ok=True)

    import xarray as xr

    lon = np.linspace(0.0, 360.0, 10)
    lat = np.linspace(-90.0, 90.0, 10)
    z = np.full((10, 10), -50.0)
    ds = xr.Dataset(
        data_vars={"z": (("y", "x"), z)},
        coords={"x": lon, "y": lat},
    )
    ds.to_netcdf(ref_dir / "etopo2.nc")

    out_dir = tmp_path / "out"
    out_dir.mkdir(parents=True, exist_ok=True)

    # 1. Default CLI run (automatically loads polygons from gridgen_data)
    cmd1 = [
        sys.executable,
        "-m",
        "gridgen.cli",
        "--name",
        "test_default",
        "--ref-dir",
        str(ref_dir),
        "--out-dir",
        str(out_dir),
        "--nx",
        "10",
        "--ny",
        "10",
    ]
    res1 = subprocess.run(cmd1, capture_output=True, text=True, check=False)
    assert res1.returncode == 0
    assert "Loaded 62 active user-defined coastal polygons." in res1.stdout

    # 2. Local polygons run
    local_poly_dir = tmp_path / "local_run"
    local_poly_dir.mkdir(parents=True, exist_ok=True)
    with open(local_poly_dir / "optional_coastal_polygons.txt", "w") as f:
        f.write("# Polygon 1: Local Poly (Level: 1, Points: 5)\n")
        f.write("0.0 0.0\n10.0 0.0\n10.0 10.0\n0.0 10.0\n0.0 0.0\n\n")
    with open(local_poly_dir / "user_polygons.flag", "w") as f:
        f.write("1 1\n")

    cmd2 = [
        sys.executable,
        "-m",
        "gridgen.cli",
        "--name",
        "test_local",
        "--ref-dir",
        str(ref_dir),
        "--out-dir",
        str(out_dir),
        "--nx",
        "10",
        "--ny",
        "10",
        "--local-polygons",
    ]
    res2 = subprocess.run(cmd2, cwd=str(local_poly_dir), capture_output=True, text=True, check=False)
    assert res2.returncode == 0
    assert "Loaded 1 active user-defined coastal polygons." in res2.stdout

    # 3. No user polygons run
    cmd3 = [
        sys.executable,
        "-m",
        "gridgen.cli",
        "--name",
        "test_no_poly",
        "--ref-dir",
        str(ref_dir),
        "--out-dir",
        str(out_dir),
        "--nx",
        "10",
        "--ny",
        "10",
        "--no-user-polygons",
    ]
    res3 = subprocess.run(cmd3, capture_output=True, text=True, check=False)
    assert res3.returncode == 0
    assert "active user-defined coastal polygons" not in res3.stdout

    # 4. All polygons run
    cmd4 = [
        sys.executable,
        "-m",
        "gridgen.cli",
        "--name",
        "test_all_poly",
        "--ref-dir",
        str(ref_dir),
        "--out-dir",
        str(out_dir),
        "--nx",
        "10",
        "--ny",
        "10",
        "--all-polygons",
    ]
    res4 = subprocess.run(cmd4, capture_output=True, text=True, check=False)
    assert res4.returncode == 0
    assert "Loaded 77 active user-defined coastal polygons." in res4.stdout


def test_caspian_sea_polygon_loading_and_masking() -> None:
    """Test that the Caspian Sea user polygon (Polygon 1) loads and successfully masks Caspian Sea points."""
    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    gridgen_data_dir = os.path.join(repo_root, "gridgen_data")

    # Load all polygons using all_polygons=True
    all_polys = load_user_polygons(ref_dir=gridgen_data_dir, all_polygons=True)
    assert len(all_polys) == 77

    # Caspian Sea is now Polygon 1
    caspian_poly = None
    for p in all_polys:
        if p["west"] < 48.0 and p["east"] > 54.0 and p["south"] < 37.0 and p["north"] > 46.0:
            caspian_poly = p
            break

    assert caspian_poly is not None, "Caspian Sea polygon must be present in loaded polygons"

    # Create a grid covering the Caspian Sea (48°E - 54°E, 38°N - 46°N)
    lon, lat = create_regular_grid(
        NX=10,
        NY=10,
        LON_START=48.0,
        LON_END=54.0,
        LAT_START=38.0,
        LAT_END=46.0,
    )
    mask = np.ones_like(lon, dtype=int)

    cleaned_mask = clean_mask(lon, lat, mask, [caspian_poly])

    # Center cell (51°E, 42°N) is well inside the Caspian Sea and should be masked dry (0)
    assert cleaned_mask[5, 5] == 0


def test_netherlands_polygons_loading_and_masking() -> None:
    """Test that Netherlands below sea level IJsselmeer and Markermeer (Polygon 2) and Wester Schelde (Polygon 14) load separately and mask points correctly."""
    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    gridgen_data_dir = os.path.join(repo_root, "gridgen_data")

    all_polys = load_user_polygons(ref_dir=gridgen_data_dir, all_polygons=True)
    assert len(all_polys) == 77

    ij_poly = all_polys[1]
    ws_poly = all_polys[13]

    assert ij_poly is not None, "Netherlands below sea level IJsselmeer and Markermeer polygon 2 must be present"
    assert ws_poly is not None, "Netherlands below sea level Wester Schelde polygon 14 must be present"

    # Test IJsselmeer point (5.2°E, 52.6°N) -> inside IJsselmeer polygon 52, outside Wester Schelde polygon 53
    lon_ij, lat_ij = create_regular_grid(
        NX=5, NY=5, LON_START=5.0, LON_END=5.4, LAT_START=52.4, LAT_END=52.8
    )
    mask_ij = np.ones_like(lon_ij, dtype=int)
    cleaned_ij = clean_mask(lon_ij, lat_ij, mask_ij, [ij_poly])
    assert cleaned_ij[2, 2] == 0
    cleaned_ij_ws = clean_mask(lon_ij, lat_ij, mask_ij, [ws_poly])
    assert cleaned_ij_ws[2, 2] == 1

    # Test Wester Schelde point (3.8°E, 51.35°N) -> inside Wester Schelde polygon 53, outside IJsselmeer polygon 52
    lon_ws, lat_ws = create_regular_grid(
        NX=3, NY=3, LON_START=3.7, LON_END=3.9, LAT_START=51.3, LAT_END=51.4
    )
    mask_ws = np.ones_like(lon_ws, dtype=int)
    cleaned_ws = clean_mask(lon_ws, lat_ws, mask_ws, [ws_poly])
    assert cleaned_ws[1, 1] == 0
    cleaned_ws_ij = clean_mask(lon_ws, lat_ws, mask_ws, [ij_poly])
    assert cleaned_ws_ij[1, 1] == 1


def test_waddenzee_polygons_loading_and_masking() -> None:
    """Test that Waddenzee polygons (15 and 16) load correctly and mask expected regions."""
    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    gridgen_data_dir = os.path.join(repo_root, "gridgen_data")

    all_polys = load_user_polygons(ref_dir=gridgen_data_dir, all_polygons=True)
    assert len(all_polys) == 77

    poly_east = all_polys[14]
    poly_north = all_polys[15]

    assert poly_east is not None, "Waddenzee East polygon 15 must be present"
    assert poly_north is not None, "Waddenzee North polygon 16 must be present"

    # Test Waddenzee East point (7.0°E, 53.6°N)
    lon_e, lat_e = create_regular_grid(
        NX=3, NY=3, LON_START=6.9, LON_END=7.1, LAT_START=53.5, LAT_END=53.7
    )
    mask_e = np.ones_like(lon_e, dtype=int)
    cleaned_e = clean_mask(lon_e, lat_e, mask_e, [poly_east])
    assert cleaned_e[1, 1] == 0

    # Test Waddenzee North point (8.6°E, 54.5°N)
    lon_n, lat_n = create_regular_grid(
        NX=3, NY=3, LON_START=8.5, LON_END=8.7, LAT_START=54.4, LAT_END=54.6
    )
    mask_n = np.ones_like(lon_n, dtype=int)
    cleaned_n = clean_mask(lon_n, lat_n, mask_n, [poly_north])
    assert cleaned_n[1, 1] == 0


def test_japan_polygons_loading_and_masking() -> None:
    """Test that Japan coastal polygons (Uchiura Bay, Mutsu Bay, Tokyo Bay, Ise Bay, Osaka Bay, Seto Inland Sea, Yamaguchi Bay, Ariake Sea, Kagoshima Bay, Omura Bay) load and mask points correctly."""
    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    gridgen_data_dir = os.path.join(repo_root, "gridgen_data")

    active_polys = load_user_polygons(ref_dir=gridgen_data_dir)
    assert len(active_polys) == 62

    japan_names = [
        "Japan: Uchiura Bay",
        "Japan: Mutsu Bay",
        "Japan: Tokyo Bay",
        "Japan: Ise Bay",
        "Japan: Osaka Bay",
        "Japan: Seto Inland Sea",
        "Japan: Yamaguchi Bay",
        "Japan: Ariake Sea",
        "Japan: Kagoshima Bay",
        "Japan: Omura Bay",
    ]

    all_polys = load_user_polygons(ref_dir=gridgen_data_dir, all_polygons=True)
    japan_polys = [p for p in all_polys if any(name in p.get("name", "") for name in japan_names)]
    assert len(japan_polys) == 10

    # Tokyo Bay test point (139.8°E, 35.5°N)
    tokyo_poly = next(p for p in japan_polys if "Tokyo Bay" in p.get("name", ""))
    lon_tb, lat_tb = create_regular_grid(
        NX=3, NY=3, LON_START=139.7, LON_END=139.9, LAT_START=35.4, LAT_END=35.6
    )
    mask_tb = np.ones_like(lon_tb, dtype=int)
    cleaned_tb = clean_mask(lon_tb, lat_tb, mask_tb, [tokyo_poly])
    assert cleaned_tb[1, 1] == 0


def test_new_polygons_loading_and_points() -> None:
    """Test loading and point counts for the 6 newly added polygons."""
    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    gridgen_data_dir = os.path.join(repo_root, "gridgen_data")

    all_polys = load_user_polygons(ref_dir=gridgen_data_dir, all_polygons=True)
    assert len(all_polys) == 77

    new_names = [
        "Aegean Sea",
        "Adriatic",
        "Sea of Azov",
        "The Gulf of Riga",
        "The Aland Islands and Turku Archipelago",
        "The inner seas in Denmark",
    ]

    found_polys = []
    for name_query in new_names:
        matches = [p for p in all_polys if name_query in p.get("name", "")]
        assert len(matches) == 1, f"Expected 1 match for polygon '{name_query}'"
        p = matches[0]
        assert len(p["x"]) >= 10, f"Polygon '{name_query}' must have at least 10 points (has {len(p['x'])})"
        found_polys.append(p)

    assert len(found_polys) == 6
