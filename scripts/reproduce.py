"""Reproduce and validate all data, tables, and figures from Section 5."""

from __future__ import annotations

from pathlib import Path
import shutil
import subprocess
import sys


SCRIPTS_DIR = Path(__file__).resolve().parent


def run(script: str, *arguments: str) -> None:
    """Run one original experiment script in a separate subprocess."""
    subprocess.run(
        [sys.executable, str(SCRIPTS_DIR / script), *arguments],
        check=True,
    )


def main() -> None:
    """Run this module as a command-line program and report its completed
    checks.
    """
    output_dir = SCRIPTS_DIR.parent / "output"
    for child in ("data", "tables", "figures"):
        target = output_dir / child
        shutil.rmtree(target, ignore_errors=True)
        target.mkdir(parents=True, exist_ok=True)

    # Run structural and dynamic stages in separate processes. This limits peak
    # memory while preserving a one-command clean reproduction workflow.
    run("run_experiments.py", "--stage", "structural")
    run("run_experiments.py", "--stage", "dynamic")
    # The peak-grid check uses prescribed seeds, not an archived CSV input.
    run("peak_grid_sensitivity.py")
    run("make_tables.py")
    run("make_figures.py")
    run("validate_outputs.py")
    print("Reproduction completed successfully.")


if __name__ == "__main__":
    main()
