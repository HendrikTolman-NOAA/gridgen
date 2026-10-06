# WAVEWATCH III (WW3) / WAVEWATCH IV (WW4) Gridgen Package
#
# Copyright 2026 National Weather Service (NWS), NOAA. All rights reserved.
# NWS often uses Generative AI (GenAI) for code development and refactoring.
# Whenever GenAI is used, NWS requires a full human review of code before it
# is added to its repositories.
#
# @author Aldgisl (Agentic AI), Jules (Agentic AI), Hendrik Tolman
# @date Initial: 2026-09-24
# @date Update: 2026-10-06

"""Unit tests for reference data population script (populate_reference_data.sh)."""

from __future__ import annotations

import os
import subprocess
import tarfile
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


def test_reference_data_gitignore():
    """Verify that reference_data/.gitignore contains entries for all populated data files."""
    repo_root = Path(__file__).parent.parent
    gitignore_path = repo_root / "reference_data" / ".gitignore"

    assert gitignore_path.exists(), "reference_data/.gitignore must exist"
    content = gitignore_path.read_text()

    expected_entries = [
        "etopo1.nc",
        "etopo2.nc",
        "coastal_bound_coarse.mat",
        "coastal_bound_full.mat",
        "coastal_bound_high.mat",
        "coastal_bound_inter.mat",
        "coastal_bound_low.mat",
        "optional_coastal_polygons.mat",
        "gridgen_addit.tar.gz",
        "ETOPO_2022_v1_60s_N90W180_bed.tif",
        "ETOPO_2022_v1_30s_N90W180_bed.tif",
    ]

    for entry in expected_entries:
        assert entry in content, f"Expected '{entry}' to be listed in reference_data/.gitignore"


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


def test_populate_script_legacy_download_or_defunct(tmp_path: Path):
    """Verify that script attempts download/extraction or outputs error for legacy dataset."""
    repo_root = Path(__file__).parent.parent
    script_path = repo_root / "populate_reference_data.sh"
    target_dir = tmp_path / "legacy_ref_data"

    result = subprocess.run(
        [str(script_path), "-d", str(target_dir), "--legacy"],
        capture_output=True,
        text=True,
        check=False,
    )

    if result.returncode == 0:
        assert "Extraction complete." in result.stdout
        assert (target_dir / "etopo1.nc").exists()
    else:
        assert "defunct and unavailable" in result.stderr
        assert "--etopo2022" in result.stderr


def test_populate_script_existing_legacy_files(tmp_path: Path):
    """Verify that script skips download/extraction when files already exist."""
    repo_root = Path(__file__).parent.parent
    script_path = repo_root / "populate_reference_data.sh"
    target_dir = tmp_path / "existing_ref_data"
    target_dir.mkdir(parents=True, exist_ok=True)

    legacy_files = [
        "etopo1.nc",
        "etopo2.nc",
        "coastal_bound_coarse.mat",
        "coastal_bound_high.mat",
        "coastal_bound_low.mat",
        "coastal_bound_full.mat",
        "coastal_bound_inter.mat",
        "optional_coastal_polygons.mat",
    ]

    for fname in legacy_files:
        (target_dir / fname).write_text("dummy content")

    result = subprocess.run(
        [str(script_path), "-d", str(target_dir), "--legacy"],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    assert "already present" in result.stdout
    assert "Skipping download and extraction" in result.stdout


def test_populate_script_existing_tarball(tmp_path: Path):
    """Verify that script extracts missing files from an existing tarball without re-downloading."""
    repo_root = Path(__file__).parent.parent
    script_path = repo_root / "populate_reference_data.sh"
    target_dir = tmp_path / "tarball_ref_data"
    target_dir.mkdir(parents=True, exist_ok=True)

    tarball_path = target_dir / "gridgen_addit.tar.gz"
    legacy_files = [
        "etopo1.nc",
        "etopo2.nc",
        "coastal_bound_coarse.mat",
        "coastal_bound_high.mat",
        "coastal_bound_low.mat",
        "coastal_bound_full.mat",
        "coastal_bound_inter.mat",
        "optional_coastal_polygons.mat",
    ]

    # Create dummy files and put into tarball
    dummy_src = tmp_path / "src_files"
    dummy_src.mkdir(parents=True, exist_ok=True)
    for fname in legacy_files:
        (dummy_src / fname).write_text(f"content of {fname}")

    with tarfile.open(tarball_path, "w:gz") as tar:
        for fname in legacy_files:
            tar.add(dummy_src / fname, arcname=fname)

    result = subprocess.run(
        [str(script_path), "-d", str(target_dir), "--legacy"],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    assert "Extracting missing legacy reference data files" in result.stdout
    assert "Extraction complete." in result.stdout
    assert "Removed tarball archive" in result.stdout

    for fname in legacy_files:
        assert (target_dir / fname).exists()
    assert not tarball_path.exists(), "Tarball file should be removed after unpacking"


def test_populate_script_clean_option(tmp_path: Path):
    """Verify that --clean removes dataset files while preserving documentation/config files."""
    repo_root = Path(__file__).parent.parent
    script_path = repo_root / "populate_reference_data.sh"
    target_dir = tmp_path / "clean_ref_data"
    target_dir.mkdir(parents=True, exist_ok=True)

    dataset_files = [
        "etopo1.nc",
        "coastal_bound_high.mat",
        "ETOPO_2022_v1_60s_N90W180_bed.tif",
    ]
    preserved_files = [
        "README.md",
        "user_polygons.flag",
        ".gitignore",
    ]

    for fname in dataset_files + preserved_files:
        (target_dir / fname).write_text(f"dummy content for {fname}")

    result = subprocess.run(
        [str(script_path), "-d", str(target_dir), "--clean"],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    assert "Cleaning up reference dataset files" in result.stdout
    assert "Cleanup complete." in result.stdout

    for fname in dataset_files:
        assert not (target_dir / fname).exists(), f"{fname} should have been deleted"

    for fname in preserved_files:
        assert (target_dir / fname).exists(), f"{fname} should have been preserved"


def test_populate_script_clean_empty_dir(tmp_path: Path):
    """Verify that --clean executes gracefully when target directory contains no dataset files."""
    repo_root = Path(__file__).parent.parent
    script_path = repo_root / "populate_reference_data.sh"
    target_dir = tmp_path / "empty_ref_data"
    target_dir.mkdir(parents=True, exist_ok=True)

    result = subprocess.run(
        [str(script_path), "-d", str(target_dir), "--clean"],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    assert "No dataset files found to remove" in result.stdout


def test_populate_script_from_external_directory(tmp_path: Path):
    """Verify populate_reference_data.sh executed from external working directory targets repo_root/reference_data by default."""
    repo_root = Path(__file__).parent.parent
    script_path = repo_root / "populate_reference_data.sh"

    result = subprocess.run(
        [str(script_path), "--gebco"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    expected_target = repo_root / "reference_data"
    assert f"Target Directory: {expected_target}" in result.stdout
