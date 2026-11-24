"""Regression checks for the numeric journal-table audit.

The negative test deliberately alters one table value in a temporary LaTeX
source. It ensures the checker really reads manuscript numbers rather than
merely checking that a file or label exists.
"""
from __future__ import annotations

import subprocess
import sys
import pytest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOL = ROOT / "scripts/validate_reported_tables.py"
SOURCE = Path(__file__).resolve().parents[2] / "manuscript/05_numerics.tex"


def test_frozen_manuscript_table_values_match_csv() -> None:
    result = subprocess.run([sys.executable, str(TOOL)], cwd=ROOT,
                            capture_output=True, text=True, check=False)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "TABLE_CROSSCHECK_PASS" in result.stdout


def test_detects_modified_real_manuscript_numeric_cell(tmp_path: Path) -> None:
    # Standalone software release can test this using the frozen source extract
    # reconstructed into an equivalent LaTeX fragment in a later release.
    if not SOURCE.is_file():
        pytest.skip("Journal source is not shipped inside the standalone software archive")
    text = SOURCE.read_text(encoding="utf-8")
    before = "Path&160,400&80,600&996&80.92"
    assert text.count(before) == 1
    modified = tmp_path / "05_numerics.tex"
    modified.write_text(text.replace(before, "Path&160,400&80,600&997&80.92"),
                        encoding="utf-8")
    result = subprocess.run([sys.executable, str(TOOL), "--manuscript", str(modified)],
                            cwd=ROOT, capture_output=True, text=True, check=False)
    assert result.returncode != 0
    assert "tab:dimension_comparison" in result.stdout + result.stderr
