# WAVEWATCH III (WW3) / WAVEWATCH IV (WW4) Gridgen Package Tests
#
# Copyright 2026 National Weather Service (NWS), NOAA. All rights reserved.
# NWS often uses Generative AI (GenAI) for code development and refactoring.
# Whenever GenAI is used, NWS requires a full human review of code before it
# is added to its repositories.
#
# @author Aldgisl (Agentic AI), Hendrik Tolman
# @author Jules (Agentic AI) (contributor)
# @date Initial: 2026-10-02
# @date Latest Update: 2026-10-09

"""Unit tests for Python grid generation runner script (run_gridgen.sh)."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path


def test_run_gridgen_help():
    """Verify that run_gridgen.sh executes and outputs help documentation."""
    repo_root = Path(__file__).parent.parent
    script_path = repo_root / "run_gridgen.sh"

    assert script_path.exists(), "run_gridgen.sh must exist"
    assert os.access(script_path, os.X_OK), "script must be executable"

    result = subprocess.run(
        [str(script_path), "--help"],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    assert "Usage: ./run_gridgen.sh" in result.stdout
    assert "Exported formats include:" in result.stdout
    assert "WW4 NetCDF-UGRID 1.0 grid" in result.stdout


def test_run_gridgen_missing_ref_dir_fails(tmp_path: Path):
    """Verify that run_gridgen.sh fails with error when reference data is missing."""
    repo_root = Path(__file__).parent.parent
    script_path = repo_root / "run_gridgen.sh"
    out_dir = tmp_path / "grid_output"
    empty_ref_dir = tmp_path / "empty_ref"
    empty_ref_dir.mkdir(parents=True, exist_ok=True)

    result = subprocess.run(
        [
            str(script_path),
            "-r",
            str(empty_ref_dir),
            "-o",
            str(out_dir),
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode != 0
    assert "Error: Reference bathymetry dataset files were not found" in result.stderr
    assert "./populate_reference_data.sh" in result.stderr
    assert "--target-dir" not in result.stderr


def test_run_gridgen_different_grid_types(tmp_path: Path):
    """Verify run_gridgen.sh supports regular (with optional rotated pole), stereographic (km and deg), and custom grid options."""
    repo_root = Path(__file__).parent.parent
    script_path = repo_root / "run_gridgen.sh"
    out_dir = tmp_path / "grid_output"
    ref_dir = tmp_path / "ref_data"
    ref_dir.mkdir(parents=True, exist_ok=True)

    import numpy as np
    import xarray as xr

    # Bathymetry reference
    lon = np.linspace(0.0, 360.0, 20)
    lat = np.linspace(-90.0, 90.0, 20)
    z = np.full((20, 20), -50.0)
    ds = xr.Dataset(
        data_vars={"z": (("lat", "lon"), z)},
        coords={"lon": lon, "lat": lat},
    )
    ds.to_netcdf(ref_dir / "etopo1.nc")

    # 1. Regular grid with rotated pole options
    res1 = subprocess.run(
        [
            str(script_path),
            "--name",
            "rot_grid",
            "-g",
            "regular",
            "--LON-START",
            "-10.0",
            "--LON-END",
            "10.0",
            "--LAT-START",
            "-10.0",
            "--LAT-END",
            "10.0",
            "--POLE-LON",
            "180.0",
            "--POLE-LAT",
            "60.0",
            "--NX",
            "10",
            "--NY",
            "10",
            "-r",
            str(ref_dir),
            "-o",
            str(out_dir),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert res1.returncode == 0
    assert (out_dir / "rot_grid_ugrid.nc").exists()

    # 2. Stereographic grid using arc degree parameters
    res2 = subprocess.run(
        [
            str(script_path),
            "--name",
            "stereo_grid",
            "-g",
            "stereographic",
            "--center-lon",
            "0.0",
            "--center-lat",
            "90.0",
            "--extent-deg",
            "4.5",
            "--nx",
            "10",
            "--ny",
            "10",
            "-r",
            str(ref_dir),
            "-o",
            str(out_dir),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert res2.returncode == 0
    assert (out_dir / "stereo_grid_ugrid.nc").exists()

    # 3. Custom grid file (.npz)
    custom_npz = tmp_path / "custom_layout.npz"
    glon, glat = np.meshgrid(np.linspace(140.0, 150.0, 5), np.linspace(40.0, 50.0, 5))
    np.savez(custom_npz, lon=glon, lat=glat)

    res3 = subprocess.run(
        [
            str(script_path),
            "--name",
            "custom_grid",
            "-g",
            "custom",
            "--custom-grid",
            str(custom_npz),
            "-r",
            str(ref_dir),
            "-o",
            str(out_dir),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert res3.returncode == 0
    assert (out_dir / "custom_grid_ugrid.nc").exists()


def test_run_gridgen_execution(tmp_path: Path):
    """Verify that run_gridgen.sh generates all grid export formats when ref_dir contains bathymetry data."""
    repo_root = Path(__file__).parent.parent
    script_path = repo_root / "run_gridgen.sh"
    out_dir = tmp_path / "grid_output"
    ref_dir = tmp_path / "ref_data"
    ref_dir.mkdir(parents=True, exist_ok=True)

    import numpy as np
    import xarray as xr

    lon = np.linspace(10.0, 12.0, 10)
    lat = np.linspace(20.0, 22.0, 10)
    z = np.full((10, 10), -50.0)
    ds = xr.Dataset(
        data_vars={"z": (("lat", "lon"), z)},
        coords={"lon": lon, "lat": lat},
    )
    ds.to_netcdf(ref_dir / "etopo1.nc")

    result = subprocess.run(
        [
            str(script_path),
            "--name",
            "test_grid",
            "--LON-START",
            "10.0",
            "--LON-END",
            "12.0",
            "--LAT-START",
            "20.0",
            "--LAT-END",
            "22.0",
            "--NX",
            "10",
            "--NY",
            "10",
            "-r",
            str(ref_dir),
            "--out-dir",
            str(out_dir),
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    assert out_dir.exists()
    assert (out_dir / "test_grid.depth_ascii").exists()
    assert (out_dir / "test_grid.maskorig_ascii").exists()
    assert (out_dir / "test_grid.obstr_lev1").exists()
    assert (out_dir / "test_grid.meta").exists()
    assert (out_dir / "test_grid_coards.nc").exists()
    assert (out_dir / "test_grid_ugrid.nc").exists()


def test_run_gridgen_with_ref_dir(tmp_path: Path):
    """Verify that run_gridgen.sh passes ref_dir and generates bathymetry from reference NetCDF when provided."""
    repo_root = Path(__file__).parent.parent
    script_path = repo_root / "run_gridgen.sh"
    out_dir = tmp_path / "grid_output"
    ref_dir = tmp_path / "ref_data"
    ref_dir.mkdir(parents=True, exist_ok=True)

    # Create dummy etopo1.nc dataset
    import numpy as np
    import xarray as xr

    lon = np.linspace(140.0, 160.0, 20)
    lat = np.linspace(44.0, 54.0, 20)
    z = np.full((20, 20), -100.0)
    ds = xr.Dataset(
        data_vars={"z": (("lat", "lon"), z)},
        coords={"lon": lon, "lat": lat},
    )
    ds.to_netcdf(ref_dir / "etopo1.nc")

    result = subprocess.run(
        [
            str(script_path),
            "--name",
            "ref_grid",
            "--LON-START",
            "140.0",
            "--LON-END",
            "160.0",
            "--LAT-START",
            "44.0",
            "--LAT-END",
            "54.0",
            "--NX",
            "20",
            "--NY",
            "20",
            "-r",
            str(ref_dir),
            "-o",
            str(out_dir),
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    assert (out_dir / "ref_grid.depth_ascii").exists()
    # Read depth file and check bathymetry is populated (e.g., -100000 after 1000 scale)
    depth_content = (out_dir / "ref_grid.depth_ascii").read_text()
    assert "-100000" in depth_content


def test_run_gridgen_missing_deps(tmp_path: Path):
    """Verify that run_gridgen.sh outputs helpful error when Python dependencies are missing."""
    repo_root = Path(__file__).parent.parent
    script_path = repo_root / "run_gridgen.sh"

    ref_dir = tmp_path / "ref_data"
    ref_dir.mkdir(parents=True, exist_ok=True)
    (ref_dir / "etopo1.nc").touch()

    # Override PATH with a directory containing a dummy python3 script that lacks numpy
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir(parents=True, exist_ok=True)
    dummy_python = bin_dir / "python3"
    dummy_python.write_text("#!/bin/sh\nexit 1\n")
    dummy_python.chmod(0o755)

    env = dict(os.environ)
    env["PATH"] = f"{bin_dir}:{env.get('PATH', '')}"

    result = subprocess.run(
        [str(script_path), "-r", str(ref_dir)],
        capture_output=True,
        text=True,
        env=env,
        check=False,
    )

    assert result.returncode != 0
    assert "Error: Required Python dependencies" in result.stderr


def test_run_gridgen_cleanup(tmp_path: Path):
    """Verify that run_gridgen.sh --cleanup removes generated output grid files and graphics files."""
    repo_root = Path(__file__).parent.parent
    script_path = repo_root / "run_gridgen.sh"
    out_dir = tmp_path / "grid_output"
    out_dir.mkdir(parents=True, exist_ok=True)

    # Create dummy output grid and graphics files (exact and suffix variants across formats)
    dummy_files = [
        out_dir / "clean_test.depth_ascii",
        out_dir / "clean_test.maskorig_ascii",
        out_dir / "clean_test.obstr_lev1",
        out_dir / "clean_test.meta",
        out_dir / "clean_test_coards.nc",
        out_dir / "clean_test_ugrid.nc",
        out_dir / "clean_test.jpg",
        out_dir / "clean_test.jpeg",
        out_dir / "clean_test.png",
        out_dir / "clean_test.pdf",
        out_dir / "clean_test.eps",
        out_dir / "clean_test.gif",
        out_dir / "clean_test_ugrid.jpg",
        out_dir / "clean_test_coards.png",
        out_dir / "clean_test_plot.pdf",
    ]
    for f in dummy_files:
        f.touch()
        assert f.exists()

    result = subprocess.run(
        [
            str(script_path),
            "--name",
            "clean_test",
            "-o",
            str(out_dir),
            "--cleanup",
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    for f in dummy_files:
        assert not f.exists(), f"File {f.name} should have been removed during cleanup"


def test_run_gridgen_from_external_directory_default_out(tmp_path: Path):
    """Verify run_gridgen.sh executed from an external working directory places output files in clone root by default."""
    repo_root = Path(__file__).parent.parent
    script_path = repo_root / "run_gridgen.sh"
    ref_dir = repo_root / "reference_data"
    ref_dir.mkdir(parents=True, exist_ok=True)

    # Ensure reference dataset file exists in reference_data
    import numpy as np
    import xarray as xr

    lon = np.linspace(140.0, 160.0, 5)
    lat = np.linspace(44.0, 54.0, 5)
    z = np.full((5, 5), -50.0)
    ds = xr.Dataset(
        data_vars={"z": (("lat", "lon"), z)},
        coords={"lon": lon, "lat": lat},
    )
    ref_file = ref_dir / "etopo1.nc"
    ds.to_netcdf(ref_file)

    grid_prefix = "ext_dir_grid"

    # Execute from tmp_path as current working directory
    result = subprocess.run(
        [
            str(script_path),
            "--name",
            grid_prefix,
            "--LON-START",
            "140.0",
            "--LON-END",
            "160.0",
            "--LAT-START",
            "44.0",
            "--LAT-END",
            "54.0",
            "--NX",
            "5",
            "--NY",
            "5",
        ],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=False,
    )

    try:
        assert result.returncode == 0
        # Check output files placed in repo_root by default, NOT in tmp_path
        assert (repo_root / f"{grid_prefix}_ugrid.nc").exists()
        assert not (tmp_path / f"{grid_prefix}_ugrid.nc").exists()
    finally:
        # Cleanup created files in repo_root
        subprocess.run(
            [str(script_path), "--name", grid_prefix, "--cleanup"],
            cwd=repo_root,
            capture_output=True,
            check=False,
        )


def test_run_gridgen_from_external_directory_custom_out(tmp_path: Path):
    """Verify run_gridgen.sh executed from external working directory respects relative user output directory option."""
    repo_root = Path(__file__).parent.parent
    script_path = repo_root / "run_gridgen.sh"
    ref_dir = repo_root / "reference_data"
    ref_dir.mkdir(parents=True, exist_ok=True)

    import numpy as np
    import xarray as xr

    lon = np.linspace(140.0, 160.0, 5)
    lat = np.linspace(44.0, 54.0, 5)
    z = np.full((5, 5), -50.0)
    ds = xr.Dataset(
        data_vars={"z": (("lat", "lon"), z)},
        coords={"lon": lon, "lat": lat},
    )
    ref_file = ref_dir / "etopo1.nc"
    ds.to_netcdf(ref_file)

    custom_out = "my_custom_out"
    grid_prefix = "ext_custom_grid"

    result = subprocess.run(
        [
            str(script_path),
            "--name",
            grid_prefix,
            "--LON-START",
            "140.0",
            "--LON-END",
            "160.0",
            "--LAT-START",
            "44.0",
            "--LAT-END",
            "54.0",
            "--NX",
            "5",
            "--NY",
            "5",
            "-o",
            custom_out,
        ],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    # Custom output directory should be created inside tmp_path (where user invoked it)
    expected_out_dir = tmp_path / custom_out
    assert expected_out_dir.exists()
    assert (expected_out_dir / f"{grid_prefix}_ugrid.nc").exists()
