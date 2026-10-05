# WAVEWATCH III (WW3) / WAVEWATCH IV (WW4) Gridgen Package Tests
#
# Copyright 2026 National Weather Service (NWS), NOAA. All rights reserved.
# NWS often uses Generative AI (GenAI) for code development and refactoring.
# Whenever GenAI is used, NWS requires a full human review of code before it
# is added to its repositories.
#
# @author Aldgisl (Agentic AI), Jules (Agentic AI), Hendrik Tolman
# @date Initial: 2026-10-02

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


def test_run_gridgen_execution(tmp_path: Path):
    """Verify that run_gridgen.sh generates all grid export formats."""
    repo_root = Path(__file__).parent.parent
    script_path = repo_root / "run_gridgen.sh"
    out_dir = tmp_path / "grid_output"

    result = subprocess.run(
        [
            str(script_path),
            "--name",
            "test_grid",
            "--dx",
            "1.0",
            "--dy",
            "1.0",
            "--lon-start",
            "10.0",
            "--lon-end",
            "12.0",
            "--lat-start",
            "20.0",
            "--lat-end",
            "22.0",
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
    assert (out_dir / "test_grid_ugrid.zarr").exists()


def test_run_gridgen_missing_deps(tmp_path: Path):
    """Verify that run_gridgen.sh outputs helpful error when Python dependencies are missing."""
    repo_root = Path(__file__).parent.parent
    script_path = repo_root / "run_gridgen.sh"

    # Override PATH with a directory containing a dummy python3 script that lacks numpy
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir(parents=True, exist_ok=True)
    dummy_python = bin_dir / "python3"
    dummy_python.write_text("#!/bin/sh\nexit 1\n")
    dummy_python.chmod(0o755)

    env = dict(os.environ)
    env["PATH"] = f"{bin_dir}:{env.get('PATH', '')}"

    result = subprocess.run(
        [str(script_path)],
        capture_output=True,
        text=True,
        env=env,
        check=False,
    )

    assert result.returncode != 0
    assert "Error: Required Python dependencies" in result.stderr
