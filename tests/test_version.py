# WAVEWATCH III (WW3) / WAVEWATCH IV (WW4) Gridgen Package Tests
#
# Copyright 2026 National Weather Service (NWS), NOAA. All rights reserved.
# NWS often uses Generative AI (GenAI) for code development and refactoring.
# Whenever GenAI is used, NWS requires a full human review of code before it
# is added to its repositories.
#
# @author Aldgisl (Agentic AI), Hendrik Tolman
# @author Jules (Agentic AI) (contributor)
# @date Initial: 2026-10-07
# @date Latest Update: 2026-10-07

"""Unit test for package version consistency across VERSION, pyproject.toml, and gridgen."""

from __future__ import annotations

import sys
from pathlib import Path

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib

import gridgen


def test_version_consistency():
    """Verify package version consistency across VERSION, pyproject.toml, and gridgen.__version__."""
    repo_root = Path(__file__).parent.parent
    version_file = repo_root / "VERSION"
    pyproject_file = repo_root / "pyproject.toml"

    assert version_file.exists(), "VERSION file must exist in root directory"
    assert pyproject_file.exists(), "pyproject.toml must exist in root directory"

    version_str = version_file.read_text().strip()
    assert version_str == "2.0.0"
    assert gridgen.__version__ == version_str

    with open(pyproject_file, "rb") as f:
        pyproject_data = tomllib.load(f)

    pyproject_version = pyproject_data.get("project", {}).get("version")
    assert pyproject_version == version_str
