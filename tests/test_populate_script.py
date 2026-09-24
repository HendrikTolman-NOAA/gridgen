# WAVEWATCH III (WW3) / WAVEWATCH IV (WW4) Gridgen Package
#
# Copyright 2026 National Weather Service (NWS), NOAA. All rights reserved.
# NWS often uses Generative AI (GenAI) for code development and refactoring.
# Whenever GenAI is used, NWS requires a full human review of code before it
# is added to its repositories.
#
# @author Aldgisl (Agentic AI), Jules (Agentic AI), Hendrik Tolman
# @date Initial: 2026-09-24

"""Unit tests for reference data population script (populate_reference_data.sh)."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path


def test_populate_script_help():
    """Verify that populate_reference_data.sh executes and returns help message."""
    repo_root = Path(__file__).parent.parent
    script_path = repo_root / "populate_reference_data.sh"

    assert script_path.exists(), "populate_reference_data.sh must exist"
    assert os.access(script_path, os.X_OK), "script must be executable"

    result = subprocess.run(
        [str(script_path), "--help"],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    assert "Usage: ./populate_reference_data.sh" in result.stdout
    assert "Authoritative External Data Sources" in result.stdout
    assert "ETOPO 2022" in result.stdout
    assert "GEBCO" in result.stdout
    assert "GSHHG" in result.stdout


def test_populate_script_target_dir(tmp_path: Path):
    """Verify that script creates target directory and executes suggestion flags."""
    repo_root = Path(__file__).parent.parent
    script_path = repo_root / "populate_reference_data.sh"
    target_dir = tmp_path / "custom_ref_data"

    result = subprocess.run(
        [str(script_path), "-d", str(target_dir), "--gebco", "--gshhg"],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    assert target_dir.exists()
    assert "SUGGESTION: Newer Authoritative Bathymetry Source - GEBCO 2024" in result.stdout
    assert "SUGGESTION: Newer Authoritative Shoreline Source - GSHHG v2.3.7" in result.stdout


def test_populate_script_defunct_legacy(tmp_path: Path):
    """Verify that script outputs error when legacy option is selected and files are missing."""
    repo_root = Path(__file__).parent.parent
    script_path = repo_root / "populate_reference_data.sh"
    target_dir = tmp_path / "legacy_ref_data"

    result = subprocess.run(
        [str(script_path), "-d", str(target_dir), "--legacy"],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 1
    assert "defunct and unavailable" in result.stderr
    assert "--etopo2022" in result.stderr
