"""Compare a fresh peak-grid experiment with the published 1.0.2 reference.

The reference file is a read-only fixture. It is never used to choose cases,
set integration parameters, or generate the new results; see the standalone
``scripts/peak_grid_sensitivity.py`` generator for those choices.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd


KEY = ["network", "seed", "weighting"]

def compare(repo: Path, destination: Path) -> pd.DataFrame:
    """Compare fresh output-grid peaks against the archived read-only
    reference.
    """
    original_path = repo / "experiments/reference/peak_grid_sensitivity_v1.0.2.csv"
    regenerated_path = repo / "output/data/peak_grid_sensitivity.csv"
    original = pd.read_csv(original_path)
    regenerated = pd.read_csv(regenerated_path)
    if len(original) != 10 or len(regenerated) != 10:
        raise AssertionError("The published study contains ten grid-refinement cases")

    # Keep published case order to preserve reproducible row-level provenance.
    observed = regenerated.set_index(KEY)
    rows = []
    for archived in original.itertuples(index=False):
        case = (archived.network, archived.seed, archived.weighting)
        selected = observed.loc[case]
        coarse = float(selected.coarse_peak)
        fine = float(selected.fine_peak)
        coarse_diff = abs(coarse - archived.coarse_peak)
        fine_diff = abs(fine - archived.fine_peak)
        rows.append({
            "network": archived.network,
            "seed": archived.seed,
            "weighting": archived.weighting,
            "coarse_peak": coarse,
            "fine_peak": fine,
            "coarse_t_peak": selected.coarse_t_peak,
            "fine_t_peak": selected.fine_t_peak,
            "abs_peak_difference": abs(fine - coarse),
            "relative_peak_difference": abs(fine - coarse) / max(abs(fine), 1e-50),
            "abs_t_peak_difference": abs(selected.fine_t_peak - selected.coarse_t_peak),
            "coarse_error_vs_archive": coarse_diff,
            "fine_error_vs_archive": fine_diff,
        })
    result = pd.DataFrame(rows)
    if max(result.coarse_error_vs_archive.max(), result.fine_error_vs_archive.max()) > 1e-9:
        raise AssertionError("Fresh peak-grid values differ from the published reference")
    destination.parent.mkdir(parents=True, exist_ok=True)
    result.to_csv(destination, index=False)
    print(json.dumps({
        "cases": len(result),
        "max_archived_peak_difference": float(max(
            result.coarse_error_vs_archive.max(), result.fine_error_vs_archive.max()
        )),
        "max_relative_grid_difference": float(result.relative_peak_difference.max()),
    }, indent=2))
    return result

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    compare(args.repo, args.out)
