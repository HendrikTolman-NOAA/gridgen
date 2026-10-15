# WAVEWATCH III (WW3) / WAVEWATCH IV (WW4) Gridgen Package Tests
#
# Copyright 2026 National Weather Service (NWS), NOAA. All rights reserved.
# NWS often uses Generative AI (GenAI) for code development and refactoring.
# Whenever GenAI is used, NWS requires a full human review of code before it
# is added to its repositories.
#
# @author Aldgisl (Agentic AI), Hendrik Tolman
# @author Jules (Agentic AI) (contributor)
# @date Initial: 2026-10-13
# @date Latest Update: 2026-10-13

"""Unit tests for Doxygen documentation build script (docs/build_docs.sh)."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path


def test_build_docs_help():
    """Verify that docs/build_docs.sh executes and outputs help documentation."""
    repo_root = Path(__file__).parent.parent
    script_path = repo_root / "docs" / "build_docs.sh"

    assert script_path.exists(), "docs/build_docs.sh must exist"
    assert os.access(script_path, os.X_OK), "script must be executable"

    result = subprocess.run(
        [str(script_path), "--help"],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    assert "Usage: ./docs/build_docs.sh [OPTIONS]" in result.stdout
    assert "Generate or clean Doxygen documentation" in result.stdout


def test_build_docs_invalid_option():
    """Verify that docs/build_docs.sh fails with unknown option error."""
    repo_root = Path(__file__).parent.parent
    script_path = repo_root / "docs" / "build_docs.sh"

    result = subprocess.run(
        [str(script_path), "--invalid-flag"],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode != 0
    assert "Error: Unknown option: --invalid-flag" in result.stderr


def test_build_docs_clean(tmp_path: Path):
    """Verify that docs/build_docs.sh --clean removes generated doc dirs without removing build_docs.sh."""
    repo_root = Path(__file__).parent.parent
    script_path = repo_root / "docs" / "build_docs.sh"

    # Create dummy generated doc folder in repo_root / docs / html
    html_dir = repo_root / "docs" / "html"
    html_dir.mkdir(parents=True, exist_ok=True)
    dummy_file = html_dir / "index.html"
    dummy_file.touch()

    assert dummy_file.exists()

    result = subprocess.run(
        [str(script_path), "--clean"],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    assert not dummy_file.exists()
    assert not html_dir.exists()
    assert script_path.exists(), "docs/build_docs.sh must remain after clean"


def test_build_docs_from_external_directory(tmp_path: Path):
    """Verify docs/build_docs.sh can be run from an external working directory."""
    repo_root = Path(__file__).parent.parent
    script_path = repo_root / "docs" / "build_docs.sh"

    result = subprocess.run(
        [str(script_path), "--help"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    assert "Usage: ./docs/build_docs.sh [OPTIONS]" in result.stdout
