"""Generate LaTeX table fragments directly from the reviewed CSV results.

These fragments accompany the independent reproduction archive; the journal
submission keeps its typeset tables self-contained. Use the generated numbers
as an explicit cross-check before updating the manuscript.
"""
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd


def latex_table(header: list[str], rows: list[list[str]]) -> str:
    """Build a plain LaTeX table fragment without changing numerical data."""
    colspec = "l" * len(header)
    lines = [f"\\begin{{tabular}}{{{colspec}}}", "\\hline",
             " & ".join(header) + " " + ("\\" * 2), "\\hline"]
    for row in rows:
        lines.append(" & ".join(row) + " " + ("\\" * 2))
    lines.extend(["\\hline", "\\end{tabular}", ""])
    return "\n".join(lines)


def render(repo: Path) -> None:
    """Generate self-contained LaTeX table fragments from revised CSV data."""
    data = repo / "experiments/data"
    output = repo / "experiments/tables"
    output.mkdir(parents=True, exist_ok=True)

    structure = pd.read_csv(data / "structural_benchmarks.csv")
    rows = []
    for record in structure[structure.n == 100].itertuples(index=False):
        rows.append([record.network, str(int(record.symmetric_d2)),
                     f"{record.graph_d2:.2f}", str(int(record.symmetric_d3)),
                     f"{record.graph_d3:.2f}"])
    (output / "symmetric_benchmarks.tex").write_text(latex_table(
        ["Network", "Symmetric d=2", "Graph d=2", "Symmetric d=3", "Graph d=3"], rows))

    bounds = pd.read_csv(data / "refined_residual_summary.csv")
    rows = [[r.network, r.weighting, f"{r.E2_peak_mean:.5f}",
             f"{r.B_original_mean:.5f}", f"{r.B_refined_mean:.5f}",
             f"{r.ratio_new_mean:.5f}"] for r in bounds.itertuples(index=False)]
    (output / "refined_residuals.tex").write_text(latex_table(
        ["Network", "Weighting", "Observed peak", "Old bound", "Revised bound", "Ratio"], rows))

    sensitivity = pd.read_csv(data / "source_node_sensitivity.csv")
    rows = [[r.network, r.weighting, r.initial_position,
             f"{r.E2_max:.5f}", f"{r.t_peak:.2f}",
             f"{r.E2_RMS_max:.5f}"] for r in sensitivity.itertuples(index=False)]
    (output / "initial_node_sensitivity.tex").write_text(latex_table(
        ["Network", "Weighting", "Seed location", "Peak", "Peak time", "RMS peak"], rows))
    print("Generated three revision LaTeX table fragments from CSV results")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, required=True)
    args = parser.parse_args()
    render(args.repo)
