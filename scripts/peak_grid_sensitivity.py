"""Recompute the ten published peak-grid checks without archived inputs.

The ten fixed graph/weighting cases below were selected for the original
study. Each is evaluated on two output grids of the *same* SEIR solution:
Delta t = 0.15 and 0.075. The CSV is generated directly from the ODE, never
from a previously saved CSV. Grid peaks are not continuous-time maxima.

Four path/star cases and six random-graph cases make ten comparisons in
total; one random seed is intentionally used under both weighting schemes. Random seeds are explicit so future software versions can reproduce
precisely the same contact supports.
"""
from __future__ import annotations

from pathlib import Path
import numpy as np
import pandas as pd

from config import DATA_DIR, BETA, SIGMA, GAMMA
from graph_topologies import (
    normalize_incoming_transmission_intensity,
    path_graph,
    sparse_random_graph,
    star_graph,
)
from residuals import first_grid_peak, residual_time_series
from seir_network import SEIRParameters, localized_initial_condition, simulate_seir

# Frozen cases from the archived 1.0.2 grid-refinement experiment. Keeping
# these selection choices in source code avoids an input dependency on output/.
CASES = (
    ("Path", None, "unit"),
    ("Star", None, "unit"),
    ("Path", None, "fixed_incoming_transmission_intensity"),
    ("Star", None, "fixed_incoming_transmission_intensity"),
    ("Sparse random", 278541765, "fixed_incoming_transmission_intensity"),
    ("Sparse random", 278541765, "unit"),
    ("Sparse random", 2239794111, "unit"),
    ("Sparse random", 2836813553, "fixed_incoming_transmission_intensity"),
    ("Sparse random", 3166108021, "fixed_incoming_transmission_intensity"),
    ("Sparse random", 3491596746, "unit"),
)


def graph_for_case(network: str, seed: int | None, n: int):
    """Return the exact directed support prescribed by a published case."""
    if network == "Path":
        return path_graph(n)
    if network == "Star":
        return star_graph(n)
    if network == "Sparse random" and seed is not None:
        return sparse_random_graph(n, 4.0, 1.0, 1.0, seed, 0)
    raise ValueError(f"Unsupported peak-grid case: {network}, {seed}")


def compute_peak_grid(output: Path = DATA_DIR) -> pd.DataFrame:
    """Integrate both grids and write the comparison used in Section 5."""
    parameters = SEIRParameters(beta=BETA, sigma=SIGMA, gamma=GAMMA)
    n = 100
    x0 = localized_initial_condition(n)
    rows = []
    for network, seed, weighting in CASES:
        graph = graph_for_case(network, seed, n)
        if weighting == "fixed_incoming_transmission_intensity":
            graph = normalize_incoming_transmission_intensity(graph, 1.0)

        peaks = []
        for dt in (0.15, 0.075):
            # The endpoint is included: 3201 and 6401 equally spaced samples.
            sample_count = int(round(480.0 / dt)) + 1
            trajectory = simulate_seir(
                graph.adjacency, parameters, x0, 480.0, sample_count
            )
            residual = residual_time_series(trajectory.y, graph.adjacency, parameters)
            peaks.append(first_grid_peak(trajectory.t, residual))

        (coarse_peak, coarse_time), (fine_peak, fine_time) = peaks
        abs_difference = abs(fine_peak - coarse_peak)
        rows.append(
            {
                "network": network,
                "seed": seed if seed is not None else np.nan,
                "weighting": weighting,
                "coarse_dt": 0.15,
                "fine_dt": 0.075,
                "coarse_peak": coarse_peak,
                "fine_peak": fine_peak,
                "abs_peak_difference": abs_difference,
                "relative_peak_difference": abs_difference / max(abs(fine_peak), 1e-50),
                "coarse_t_peak": coarse_time,
                "fine_t_peak": fine_time,
                "abs_t_peak_difference": abs(fine_time - coarse_time),
            }
        )
    frame = pd.DataFrame.from_records(rows)
    output.mkdir(parents=True, exist_ok=True)
    destination = output / "peak_grid_sensitivity.csv"
    frame.to_csv(destination, index=False)
    print(f"Peak-grid validation data: {len(frame)} cases -> {destination}")
    return frame


if __name__ == "__main__":
    compute_peak_grid()
