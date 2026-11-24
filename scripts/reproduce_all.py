"""Build the original and revised SEIR numerical results from a clean tree.

Run this script from any working directory. It first regenerates the results of
Zenodo release 1.0.2, including the independently specified peak-grid cases.
It then generates the material added for the CNSNS revision: structural
benchmarks, graph-specific bounds, seed-position sensitivity, sparse lifted
operators, larger networks, and the revised dimension figure and tables.

All source-code paths are resolved relative to this file. Saved CSVs serve only
as regression references, never as inputs to the computations they certify.
Timing and memory measurements necessarily vary between computers.
"""
from __future__ import annotations

import argparse
import json
import os
import platform
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import matplotlib
import numpy
import pandas
import scipy

ROOT = Path(__file__).resolve().parents[1]
EXPERIMENTS = ROOT / "experiments"
SCRIPTS = EXPERIMENTS / "scripts"
DATA = EXPERIMENTS / "data"
FIGURES = EXPERIMENTS / "figures"
TABLES = EXPERIMENTS / "tables"
RESULTS = EXPERIMENTS / "results"


def run_file(path: Path, *arguments: str) -> None:
    """Execute one stage in its own process to limit peak memory usage."""
    command = [sys.executable, str(path), *map(str, arguments)]
    print("RUN", " ".join(command[1:]), flush=True)
    subprocess.run(command, cwd=ROOT, check=True)


def clear_generated_experiments() -> None:
    """Remove only generated results; retain source and regression fixtures."""
    for directory in (DATA, FIGURES, TABLES, RESULTS):
        shutil.rmtree(directory, ignore_errors=True)
        directory.mkdir(parents=True, exist_ok=True)


def reproduce_all() -> None:
    """Execute every original and experiment and record the software
    environment.
    """
    clear_generated_experiments()

    # Recompute the published experiments first; scripts/reproduce.py cleans
    # output/ and rebuilds the baseline, the peak grid, tables, and figures.
    run_file(ROOT / "scripts/reproduce.py")

    common = ("--repo", str(ROOT))
    run_file(SCRIPTS / "structural_benchmarks.py", *common,
             "--out", str(DATA / "structural_benchmarks.csv"))
    run_file(SCRIPTS / "graph_residual_bounds.py", *common,
             "--out", str(DATA / "refined_residual_summary.csv"),
             "--rawout", str(DATA / "refined_bounds_by_realization.csv"))
    run_file(SCRIPTS / "source_sensitivity.py", *common,
             "--out", str(DATA / "source_node_sensitivity.csv"),
             "--randomout", str(DATA / "random_normalized_rms.csv"))
    run_file(SCRIPTS / "dictionary_performance.py", *common,
             "--out", str(DATA / "dictionary_build_runs.csv"))
    run_file(SCRIPTS / "sparse_operator.py", *common,
             "--out", str(DATA / "sparse_operator_costs.csv"))
    run_file(SCRIPTS / "large_networks.py", *common,
             "--out", str(DATA / "large_networks.csv"))
    run_file(SCRIPTS / "peak_grid_check.py", *common,
             "--out", str(DATA / "peak_grid_refinement_check.csv"))

    # additional: homogeneous, small-scale comparisons; observed face-to-face workplace
    # contact structure as a non-calibrated fixed-network benchmark; and finite-order trajectory diagnostics.
    run_file(SCRIPTS / "carleman_cost_comparison.py", *common,
             "--out", str(DATA / "carleman_costs.csv"), "--repeats", "5")
    run_file(SCRIPTS / "sociopatterns_workplace.py", *common,
             "--out", str(DATA), "--repeats", "30")
    run_file(SCRIPTS / "truncation_accuracy.py", *common,
             "--out", str(DATA / "truncation_accuracy.csv"))

    run_file(SCRIPTS / "make_dimension_figure.py",
             "--source", str(DATA / "structural_benchmarks.csv"),
             "--out", str(FIGURES / "figure_2_dimension_comparison.pdf"))
    run_file(SCRIPTS / "make_experiment_tables.py", "--repo", str(ROOT))

    # Exact algebraic tests complement the floating-point experimental checks.
    run_file(EXPERIMENTS / "theory_tests/reachable_closure_check.py")
    run_file(EXPERIMENTS / "theory_tests/verify_refinements.py")
    run_file(EXPERIMENTS / "theory_tests/high_order_example.py")
    run_file(SCRIPTS / "validate_experimental_data.py", *common, "--results", str(DATA))
    run_file(ROOT / "scripts/validate_outputs.py")
    run_file(ROOT / "scripts/validate_manuscript_alignment.py")
    # Check the frozen journal table extract against current CSV values. The
    # exact LaTeX source is checked separately by --manuscript during closure.
    run_file(ROOT / "scripts/validate_reported_tables.py")
    run_file(ROOT / "scripts/check_release_metadata.py")

    report = {
        "status": "PASS",
        "release_version": "1.0.4",
        "software": {
            "python": platform.python_version(),
            "numpy": numpy.__version__,
            "scipy": scipy.__version__,
            "pandas": pandas.__version__,
            "matplotlib": matplotlib.__version__,
            "platform": platform.platform(),
            "architecture": platform.machine(),
            "logical_cpu_count": os.cpu_count(),
        },
        "random_generator": "numpy.random.default_rng (PCG64)",
        "random_master_seed": 12345,
        "scope": "original experiments, structural and computational comparisons, workplace contact data, and finite-order prediction errors",
        "generated_files": {
            "original_output": sum(p.is_file() for p in (ROOT / "output").rglob("*")),
            "additional_data": len(list(DATA.glob("*.csv"))),
            "additional_figures": len(list(FIGURES.glob("*.pdf"))),
            "additional_tables": len(list(TABLES.glob("*.tex"))),
        },
        "limitations": [
            "time and peak RSS vary by hardware and runtime",
            "full symmetric Carleman benchmark is timed only for small n=4,8,12",
            "recorded face-to-face contacts are aggregated into a static support, not used as time-varying epidemiological rates",
            "model diagonal channels are assumed rather than measured; no epidemiological calibration",
            "accuracy experiments establish no convergence across truncation orders",
            "larger networks are synthetic and not epidemiologically calibrated",
        ],
    }
    report_path = RESULTS / "reproduction_report.json"
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print("FULL_REPRODUCTION_PASS", report_path)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args()
    reproduce_all()
