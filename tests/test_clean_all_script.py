# WAVEWATCH III (WW3) / WAVEWATCH IV (WW4) Gridgen Package Tests
#
# Copyright 2026 National Weather Service (NWS), NOAA. All rights reserved.
# NWS often uses Generative AI (GenAI) for code development and refactoring.
# Whenever GenAI is used, NWS requires a full human review of code before it
# is added to its repositories.
#
# @author Aldgisl (Agentic AI), Hendrik Tolman
# @author Jules (Agentic AI) (contributor)
# @date Initial: 2026-10-15
# @date Latest Update: 2026-10-15

"""Unit tests for master repository cleanup script (clean_all.sh)."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path


def test_clean_all_help():
    """Verify that clean_all.sh executes and outputs help documentation."""
    repo_root = Path(__file__).parent.parent
    script_path = repo_root / "clean_all.sh"

    assert script_path.exists(), "clean_all.sh must exist"
    assert os.access(script_path, os.X_OK), "script must be executable"

    result = subprocess.run(
        [str(script_path), "--help"],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    assert "Usage: ./clean_all.sh" in result.stdout
    assert "Master cleanup utility script" in result.stdout


def test_clean_all_execution(tmp_path: Path):
    """Verify that clean_all.sh removes generated grid files, graphics, docs, and build cache artifacts."""
    repo_root = Path(__file__).parent.parent
    script_path = repo_root / "clean_all.sh"

    # Create dummy files to clean in tmp_path
    dummy_files = [
        tmp_path / "test.depth_ascii",
        tmp_path / "test.maskorig_ascii",
        tmp_path / "test.obstr_lev1",
        tmp_path / "test.meta",
        tmp_path / "test_coards.nc",
        tmp_path / "test_ugrid.nc",
        tmp_path / "test.jpg",
        tmp_path / "test.png",
        tmp_path / "test.pdf",
    ]
    for f in dummy_files:
        f.touch()
        assert f.exists()

    # Create dummy cache/build dirs
    cache_dir = tmp_path / ".pytest_cache"
    cache_dir.mkdir(parents=True, exist_ok=True)
    pycache_dir = tmp_path / "subdir" / "__pycache__"
    pycache_dir.mkdir(parents=True, exist_ok=True)
    (pycache_dir / "mod.pyc").touch()

    assert cache_dir.exists()
    assert pycache_dir.exists()

    result = subprocess.run(
        [str(script_path)],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    assert "Master cleanup finished successfully." in result.stdout

    for f in dummy_files:
        assert not f.exists(), f"File {f.name} should have been removed"

    assert not cache_dir.exists()
    assert not pycache_dir.exists()
