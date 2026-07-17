"""Validate structural invariance, dynamic sensitivity, and generated outputs."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from config import (
    DATA_DIR,
    DYNAMIC_NETWORK_SIZE,
    FINAL_ACTIVE_TOLERANCE,
    FINAL_RESIDUAL_TOLERANCE,
    FIGURES_DIR,
    FINAL_TIME,
    FIXED_INCOMING_TRANSMISSION_INTENSITY,
    FIXED_INCOMING_TRANSMISSION_INTENSITY_WEIGHTING,
    MASTER_SEED,
    INITIAL_SOURCE_NODE,
    REQUIRE_INITIAL_SOURCE_OUTGOING_CHANNEL,
    RANDOM_MEAN_DEGREE,
    RANDOM_REALIZATIONS,
    TABLES_DIR,
    TIME_POINTS,
    UNIT_WEIGHTING,
)
from graph_topologies import (
    normalize_incoming_transmission_intensity,
    path_graph,
    sparse_random_ensemble,
    star_graph,
)
from lifting_metrics import cubic_dictionary_metrics, edge_quadratic_dimension


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def validate_support_invariance() -> None:
    graphs = [
        path_graph(DYNAMIC_NETWORK_SIZE),
        star_graph(DYNAMIC_NETWORK_SIZE),
        *sparse_random_ensemble(
            n=DYNAMIC_NETWORK_SIZE,
            realizations=RANDOM_REALIZATIONS,
            mean_degree=RANDOM_MEAN_DEGREE,
            off_diagonal_weight=1.0,
            diagonal_weight=1.0,
            seed=MASTER_SEED + DYNAMIC_NETWORK_SIZE,
            initial_source_node=INITIAL_SOURCE_NODE,
            require_initial_source_outgoing_channel=REQUIRE_INITIAL_SOURCE_OUTGOING_CHANNEL,
        ),
    ]
    for graph in graphs:
        normalized = normalize_incoming_transmission_intensity(
            graph, FIXED_INCOMING_TRANSMISSION_INTENSITY
        )
        require(
            np.array_equal(graph.adjacency > 0.0, normalized.adjacency > 0.0),
            f"Support changed for {graph.name}.",
        )
        require(
            np.allclose(
                normalized.adjacency.sum(axis=1),
                FIXED_INCOMING_TRANSMISSION_INTENSITY,
                rtol=0.0,
                atol=1e-12,
            ),
            f"Incoming transmission intensity failed for {graph.name}.",
        )
        require(
            edge_quadratic_dimension(graph.adjacency)
            == edge_quadratic_dimension(normalized.adjacency),
            f"First dictionary dimension changed for {graph.name}.",
        )

    # The dictionary generator depends only on support. Check representative
    # deterministic and random cases explicitly, including the hub topology.
    for graph in (graphs[0], graphs[1], graphs[2], graphs[-1]):
        normalized = normalize_incoming_transmission_intensity(
            graph, FIXED_INCOMING_TRANSMISSION_INTENSITY
        )
        require(
            cubic_dictionary_metrics(graph.adjacency)
            == cubic_dictionary_metrics(normalized.adjacency),
            f"Cubic dictionary changed for {graph.name}.",
        )


def validate_csv_outputs() -> None:
    summary = pd.read_csv(DATA_DIR / "residual_sensitivity_summary.csv")
    curves = pd.read_csv(DATA_DIR / "residual_sensitivity_timeseries.csv")
    raw = pd.read_csv(DATA_DIR / "sparse_random_residual_realizations.csv")
    validation = pd.read_csv(DATA_DIR / "simulation_validation.csv")
    unit_summary = pd.read_csv(DATA_DIR / "residual_summary.csv")

    expected_weightings = {
        UNIT_WEIGHTING,
        FIXED_INCOMING_TRANSMISSION_INTENSITY_WEIGHTING,
    }
    expected_networks = {"Path", "Star", "Sparse random"}
    require(set(summary["weighting"]) == expected_weightings, "Missing weighting case.")
    require(set(summary["network"]) == expected_networks, "Missing network summary.")
    require(len(summary) == 6, "Unexpected residual-summary row count.")
    require(set(curves["weighting"]) == expected_weightings, "Missing curve case.")
    require(set(raw["weighting"]) == expected_weightings, "Missing raw case.")
    require(len(raw) == 2 * RANDOM_REALIZATIONS, "Unexpected random raw row count.")

    curve_counts = curves.groupby(["weighting", "network"]).size()
    require(
        bool((curve_counts == TIME_POINTS).all()),
        "A residual curve has an unexpected number of time samples.",
    )
    require(np.isclose(float(curves["t"].min()), 0.0), "Unexpected initial time.")
    require(np.isclose(float(curves["t"].max()), FINAL_TIME), "Unexpected final time.")

    normalized_raw = raw[
        raw["weighting"] == FIXED_INCOMING_TRANSMISSION_INTENSITY_WEIGHTING
    ]
    require(
        np.allclose(
            normalized_raw["row_sum_min"],
            FIXED_INCOMING_TRANSMISSION_INTENSITY,
            atol=1e-12,
        ),
        "Normalized minimum row sum is not one.",
    )
    require(
        np.allclose(
            normalized_raw["row_sum_max"],
            FIXED_INCOMING_TRANSMISSION_INTENSITY,
            atol=1e-12,
        ),
        "Normalized maximum row sum is not one.",
    )

    random_summary = summary[summary["network"] == "Sparse random"]
    require(np.all(random_summary["t_peak_std"] > 0.0), "Peak-time spread is missing.")
    deterministic = summary[summary["network"] != "Sparse random"]
    require(np.allclose(deterministic["t_peak_std"], 0.0), "Deterministic spread is nonzero.")

    unit_from_combined = (
        summary[summary["weighting"] == UNIT_WEIGHTING]
        .drop(columns=["weighting", "weighting_label"])
        .reset_index(drop=True)
    )
    pd.testing.assert_frame_equal(unit_summary, unit_from_combined, check_exact=True)

    require(
        float(validation["maximum_local_mass_error"].max()) <= 1e-8,
        "Mass-conservation tolerance failed.",
    )
    require(
        float(validation["minimum_compartment_value"].min()) >= -1e-8,
        "Nonnegativity tolerance failed.",
    )
    require(np.all(summary["E2_max"] <= summary["B2"]), "A residual exceeds its bound.")
    require(
        float(validation["maximum_final_residual"].max()) <= FINAL_RESIDUAL_TOLERANCE,
        "A residual trajectory has not reached the extinction phase.",
    )
    require(
        float(validation["maximum_final_active_fraction"].max())
        <= FINAL_ACTIVE_TOLERANCE,
        "An SEIR trajectory has not reached the extinction phase.",
    )
    require(
        float(summary["E2_final"].max()) <= FINAL_RESIDUAL_TOLERANCE,
        "A summarized residual has not decayed below the extinction tolerance.",
    )
    require(
        float(summary["active_final_max"].max()) <= FINAL_ACTIVE_TOLERANCE,
        "A summarized active fraction has not decayed below the extinction tolerance.",
    )

    # The pre-specified ensemble admissibility criterion must hold for every
    # stored random realization.
    require(
        bool((raw["initial_source_outgoing_channels"] >= 1).all()),
        "A random realization violates the initial-source admissibility criterion.",
    )


def validate_tables_and_figures() -> None:
    required_tables = {
        "network_quantities.tex",
        "dimension_comparison.tex",
        "residual_summary.tex",
        "cubic_dictionary_size.tex",
    }
    required_figures = {
        "dimension_comparison.pdf",
        "residual_dynamics_unit.pdf",
        "residual_dynamics_fixed_incoming_transmission_intensity.pdf",
        "higher_order_dictionary_size.pdf",
    }
    require(required_tables <= {p.name for p in TABLES_DIR.glob("*.tex")}, "Missing table.")
    require(required_figures <= {p.name for p in FIGURES_DIR.glob("*.pdf")}, "Missing figure.")

    residual_table = (TABLES_DIR / "residual_summary.tex").read_text(encoding="utf-8")
    require("$\\pm$" in residual_table, "Random-ensemble uncertainty is absent from table.")
    require(
        "Fixed incoming intensity" in residual_table,
        "Fixed-intensity sensitivity absent from table.",
    )
    require(
        residual_table.count(r"\begin{tabular}") == 1,
        "The residual results were split across multiple tabular environments.",
    )

    figure_source = (Path(__file__).resolve().parent / "make_figures.py").read_text(
        encoding="utf-8"
    )
    require("set_title(" not in figure_source, "Embedded figure titles remain in source.")
    require("FINAL_TIME" in figure_source, "Residual figure does not use the configured horizon.")


def main() -> None:
    validate_support_invariance()
    validate_csv_outputs()
    validate_tables_and_figures()
    print("All structural, numerical, table, and figure validations passed.")


if __name__ == "__main__":
    main()
