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

"""Unit test for single-source package version definition in gridgen."""

from __future__ import annotations

import sys
from pathlib import Path

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib

import gridgen


def test_package_version():
    """Verify single-source version definition in gridgen.__version__ and pyproject.toml."""
    assert gridgen.__version__ == "3.0.0"

    repo_root = Path(__file__).parent.parent
    pyproject_file = repo_root / "pyproject.toml"
    version_file = repo_root / "VERSION"

    assert not version_file.exists(), (
        "VERSION file must not exist (single source of truth in gridgen.__version__)"
    )
    assert pyproject_file.exists(), "pyproject.toml must exist in root directory"

    with open(pyproject_file, "rb") as f:
        pyproject_data = tomllib.load(f)

    # Verify setuptools dynamic version configuration points to gridgen.__version__
    dynamic_attrs = (
        pyproject_data.get("tool", {}).get("setuptools", {}).get("dynamic", {})
    )
    assert dynamic_attrs.get("version", {}).get("attr") == "gridgen.__version__"
