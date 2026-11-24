"""Generate every CSV file used by the numerical illustrations in Section 5.

The script runs three structural experiments and two dynamic weighting cases:

1. quadratic lifting dimensions for several network sizes;
2. first-closure residuals at ``n = 100`` with unit channel weights;
3. the same residual experiment after fixing every row's total incoming transmission intensity;
4. linearly closed cubic dictionary sizes.

The sensitivity changes weights but preserves graph support. Consequently, all
structural dictionary dimensions are shared by the two dynamic weighting cases.
The same sparse-random graph realizations and seeds are reused throughout.
"""

from __future__ import annotations

from collections.abc import Iterable
from concurrent.futures import ProcessPoolExecutor
import argparse
import os

# Avoid BLAS thread oversubscription when independent graph realizations are
# evaluated in separate worker processes.
os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")
os.environ.setdefault("NUMEXPR_NUM_THREADS", "1")

import numpy as np
import pandas as pd

from config import (
    BETA,
    CONSERVATION_TOLERANCE,
    FINAL_ACTIVE_TOLERANCE,
    FINAL_RESIDUAL_TOLERANCE,
    DATA_DIR,
    DIAGONAL_WEIGHT,
    DYNAMIC_NETWORK_SIZE,
    DYNAMIC_WEIGHTING_SCHEMES,
    FINAL_TIME,
    FIXED_INCOMING_TRANSMISSION_INTENSITY,
    FIXED_INCOMING_TRANSMISSION_INTENSITY_WEIGHTING,
    GAMMA,
    MASTER_SEED,
    INITIAL_SOURCE_NODE,
    REQUIRE_INITIAL_SOURCE_OUTGOING_CHANNEL,
    NETWORK_SIZES,
    NONNEGATIVITY_TOLERANCE,
    OFF_DIAGONAL_WEIGHT,
    RANDOM_MEAN_DEGREE,
    RANDOM_REALIZATIONS,
    SIGMA,
    TIME_POINTS,
    UNIT_WEIGHTING,
    WEIGHTING_LABELS,
)
from graph_topologies import (
    GraphData,
    normalize_incoming_transmission_intensity,
    path_graph,
    sparse_random_ensemble,
    star_graph,
)
from lifting_metrics import (
    complete_cubic_dimension,
    complete_quadratic_dimension,
    cubic_dictionary_metrics,
    edge_quadratic_dimension,
    network_metrics,
)
from residuals import first_grid_peak, residual_bound, residual_time_series, time_average
from seir_network import SEIRParameters, localized_initial_condition, simulate_seir


RandomEnsembles = dict[int, list[GraphData]]
CubicCache = dict[tuple[int, int], dict[str, int]]


def deterministic_graphs(n: int) -> list[GraphData]:
    """Return the path and star supports used at network size ``n``."""
    return [
        path_graph(n, OFF_DIAGONAL_WEIGHT, DIAGONAL_WEIGHT),
        star_graph(n, OFF_DIAGONAL_WEIGHT, DIAGONAL_WEIGHT),
    ]


# All structural and dynamic scenarios reuse the same accepted supports.
def build_random_ensembles() -> RandomEnsembles:
    """Build the reproducible sparse-random ensembles for all network sizes."""
    return {
        n: sparse_random_ensemble(
            n=n,
            realizations=RANDOM_REALIZATIONS,
            mean_degree=RANDOM_MEAN_DEGREE,
            off_diagonal_weight=OFF_DIAGONAL_WEIGHT,
            diagonal_weight=DIAGONAL_WEIGHT,
            seed=MASTER_SEED + n,
            initial_source_node=INITIAL_SOURCE_NODE,
            require_initial_source_outgoing_channel=REQUIRE_INITIAL_SOURCE_OUTGOING_CHANNEL,
        )
        for n in NETWORK_SIZES
    }


def graph_for_weighting(graph: GraphData, weighting: str) -> GraphData:
    """Return ``graph`` under the requested dynamic weighting scheme."""
    if weighting == UNIT_WEIGHTING:
        return graph
    if weighting == FIXED_INCOMING_TRANSMISSION_INTENSITY_WEIGHTING:
        normalized = normalize_incoming_transmission_intensity(
            graph, FIXED_INCOMING_TRANSMISSION_INTENSITY
        )
        if edge_quadratic_dimension(normalized.adjacency) != edge_quadratic_dimension(
            graph.adjacency
        ):
            raise RuntimeError("A weighting change altered the first dictionary size.")
        return normalized
    raise ValueError(f"Unknown weighting scheme: {weighting}")


def mean_and_sample_std(values: Iterable[float]) -> tuple[float, float]:
    """Return the arithmetic mean and sample standard deviation."""
    array = np.asarray(list(values), dtype=float)
    mean = float(np.mean(array))
    std = float(np.std(array, ddof=1)) if array.size > 1 else 0.0
    return mean, std


def quadratic_dimension_results(ensembles: RandomEnsembles) -> pd.DataFrame:
    """Compute the data behind Table 2 and Figure 2 of the article."""
    rows: list[dict[str, float | int | str]] = []

    for n in NETWORK_SIZES:
        full_dimension = complete_quadratic_dimension(n)

        for graph in deterministic_graphs(n):
            edge_dimension = edge_quadratic_dimension(graph.adjacency)
            rows.append(
                {
                    "network": graph.name,
                    "n": n,
                    "m": graph.m,
                    "m_std": 0.0,
                    "m_diagonal": graph.diagonal_channels,
                    "m_off_diagonal": graph.off_diagonal_channels,
                    "D_full_2": full_dimension,
                    "D_edge_2": edge_dimension,
                    "D_edge_2_std": 0.0,
                    "reduction_factor": full_dimension / edge_dimension,
                    "reduction_factor_std": 0.0,
                }
            )

        random_rows = []
        for graph in ensembles[n]:
            edge_dimension = edge_quadratic_dimension(graph.adjacency)
            random_rows.append(
                {
                    "m": graph.m,
                    "m_diagonal": graph.diagonal_channels,
                    "m_off_diagonal": graph.off_diagonal_channels,
                    "D_edge_2": edge_dimension,
                    "reduction_factor": full_dimension / edge_dimension,
                }
            )
        random_frame = pd.DataFrame(random_rows)

        m_mean, m_std = mean_and_sample_std(random_frame["m"])
        edge_mean, edge_std = mean_and_sample_std(random_frame["D_edge_2"])
        factor_mean, factor_std = mean_and_sample_std(
            random_frame["reduction_factor"]
        )

        rows.append(
            {
                "network": "Sparse random",
                "n": n,
                "m": m_mean,
                "m_std": m_std,
                "m_diagonal": float(random_frame["m_diagonal"].mean()),
                "m_off_diagonal": float(random_frame["m_off_diagonal"].mean()),
                "D_full_2": full_dimension,
                "D_edge_2": edge_mean,
                "D_edge_2_std": edge_std,
                "reduction_factor": factor_mean,
                "reduction_factor_std": factor_std,
            }
        )

    return pd.DataFrame(rows)


def network_quantity_results(
    ensembles: RandomEnsembles,
    n: int = DYNAMIC_NETWORK_SIZE,
) -> pd.DataFrame:
    """Compute the unit-weight network quantities displayed in Table 1."""
    rows: list[dict[str, float | int | str]] = []

    for graph in deterministic_graphs(n):
        metrics = network_metrics(graph.adjacency)
        rows.append(
            {
                "network": graph.name,
                **metrics,
                "m_std": 0.0,
                "Delta_in_std": 0.0,
                "delta_max_in_std": 0.0,
            }
        )

    random_frame = pd.DataFrame(
        network_metrics(graph.adjacency) for graph in ensembles[n]
    )
    m_mean, m_std = mean_and_sample_std(random_frame["m"])
    degree_mean, degree_std = mean_and_sample_std(random_frame["Delta_in"])
    weighted_mean, weighted_std = mean_and_sample_std(
        random_frame["delta_max_in"]
    )

    rows.append(
        {
            "network": "Sparse random",
            "n": n,
            "m": m_mean,
            "m_std": m_std,
            "m_diagonal": float(random_frame["m_diagonal"].mean()),
            "m_off_diagonal": float(random_frame["m_off_diagonal"].mean()),
            "Delta_in": degree_mean,
            "Delta_in_std": degree_std,
            "delta_max_in": weighted_mean,
            "delta_max_in_std": weighted_std,
        }
    )

    return pd.DataFrame(rows)


def validate_trajectory(
    trajectory: np.ndarray,
    initial_state: np.ndarray,
    n: int,
) -> tuple[float, float]:
    """Check finiteness, dimensions, local mass conservation, and positivity."""
    if trajectory.ndim != 2 or trajectory.shape[0] != 4 * n:
        raise RuntimeError("The integrated trajectory has an invalid dimension.")
    if np.any(~np.isfinite(trajectory)):
        raise RuntimeError("The integrated trajectory contains nonfinite values.")

    susceptible = trajectory[0:n]
    exposed = trajectory[n : 2 * n]
    infectious = trajectory[2 * n : 3 * n]
    removed = trajectory[3 * n : 4 * n]
    local_mass = susceptible + exposed + infectious + removed

    s0 = initial_state[0:n]
    e0 = initial_state[n : 2 * n]
    i0 = initial_state[2 * n : 3 * n]
    r0 = initial_state[3 * n : 4 * n]
    initial_local_mass = s0 + e0 + i0 + r0

    maximum_mass_error = float(
        np.max(np.abs(local_mass - initial_local_mass[:, None]))
    )
    minimum_state = float(np.min(trajectory))

    if maximum_mass_error > CONSERVATION_TOLERANCE:
        raise RuntimeError("A trajectory failed the local mass-conservation check.")
    if minimum_state < -NONNEGATIVITY_TOLERANCE:
        raise RuntimeError("A trajectory failed the numerical nonnegativity check.")

    return maximum_mass_error, minimum_state


def simulate_residual(
    graph: GraphData,
    parameters: SEIRParameters,
) -> dict[str, np.ndarray | float]:
    """Simulate one graph and return its residual curve and audit quantities."""
    initial_state = localized_initial_condition(graph.n)
    solution = simulate_seir(
        adjacency=graph.adjacency,
        parameters=parameters,
        initial_state=initial_state,
        final_time=FINAL_TIME,
        time_points=TIME_POINTS,
    )
    mass_error, minimum_state = validate_trajectory(
        solution.y, initial_state, graph.n
    )
    residual = residual_time_series(solution.y, graph.adjacency, parameters)
    bound = residual_bound(graph.adjacency, parameters)
    peak, peak_time = first_grid_peak(solution.t, residual)
    average = time_average(solution.t, residual)
    final_residual = float(residual[-1])
    final_exposed = solution.y[graph.n : 2 * graph.n, -1]
    final_infectious = solution.y[2 * graph.n : 3 * graph.n, -1]
    final_active_max = float(np.max(final_exposed + final_infectious))

    if peak > bound * (1.0 + 1e-12):
        raise RuntimeError("The computed residual exceeds the theoretical bound.")

    return {
        "times": solution.t,
        "curve": residual,
        "peak": peak,
        "average": average,
        "bound": bound,
        "peak_time": peak_time,
        "final_residual": final_residual,
        "final_active_max": final_active_max,
        "maximum_mass_error": mass_error,
        "minimum_state": minimum_state,
    }


def _simulate_weighted_graph(
    payload: tuple[GraphData, str, SEIRParameters],
) -> tuple[GraphData, dict[str, np.ndarray | float]]:
    """Apply one weighting scheme and evaluate one residual trajectory."""
    base_graph, weighting, parameters = payload
    graph = graph_for_weighting(base_graph, weighting)
    return graph, simulate_residual(graph, parameters)


def _summary_row(
    weighting: str,
    network: str,
    peaks: list[float],
    averages: list[float],
    bounds: list[float],
    peak_times: list[float],
    final_residuals: list[float],
    final_active_values: list[float],
) -> dict[str, float | str]:
    """Summarize one network and weighting configuration for the results
    table.
    """
    peak_mean, peak_std = mean_and_sample_std(peaks)
    average_mean, average_std = mean_and_sample_std(averages)
    bound_mean, bound_std = mean_and_sample_std(bounds)
    ratios = [peak / bound for peak, bound in zip(peaks, bounds, strict=True)]
    ratio_mean, ratio_std = mean_and_sample_std(ratios)
    peak_time_mean, peak_time_std = mean_and_sample_std(peak_times)
    final_residual_mean, final_residual_std = mean_and_sample_std(final_residuals)
    final_active_mean, final_active_std = mean_and_sample_std(final_active_values)
    return {
        "weighting": weighting,
        "weighting_label": WEIGHTING_LABELS[weighting],
        "network": network,
        "E2_max": peak_mean,
        "E2_max_std": peak_std,
        "E2_time_average": average_mean,
        "E2_time_average_std": average_std,
        "B2": bound_mean,
        "B2_std": bound_std,
        "E2_max_over_B2": ratio_mean,
        "E2_max_over_B2_std": ratio_std,
        "t_peak": peak_time_mean,
        "t_peak_std": peak_time_std,
        "E2_final": final_residual_mean,
        "E2_final_std": final_residual_std,
        "active_final_max": final_active_mean,
        "active_final_max_std": final_active_std,
    }


def residual_results(
    ensembles: RandomEnsembles,
    n: int = DYNAMIC_NETWORK_SIZE,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Compute residual summaries, curves, raw random results, and validation."""
    parameters = SEIRParameters(beta=BETA, sigma=SIGMA, gamma=GAMMA)
    summary_rows: list[dict[str, float | str]] = []
    time_series_rows: list[dict[str, float | str]] = []
    random_rows: list[dict[str, float | int | str | None]] = []
    validation_rows: list[dict[str, float | str]] = []

    base_deterministic = deterministic_graphs(n)
    base_random = ensembles[n]

    for weighting in DYNAMIC_WEIGHTING_SCHEMES:
        scenario_validation: list[tuple[float, float, float, float]] = []

        for base_graph in base_deterministic:
            graph = graph_for_weighting(base_graph, weighting)
            result = simulate_residual(graph, parameters)
            times = np.asarray(result["times"])
            curve = np.asarray(result["curve"])
            peak = float(result["peak"])
            average = float(result["average"])
            bound = float(result["bound"])
            peak_time = float(result["peak_time"])
            final_residual = float(result["final_residual"])
            final_active_max = float(result["final_active_max"])
            mass_error = float(result["maximum_mass_error"])
            minimum_state = float(result["minimum_state"])
            scenario_validation.append(
                (mass_error, minimum_state, final_residual, final_active_max)
            )

            summary_rows.append(
                _summary_row(
                    weighting,
                    graph.name,
                    [peak],
                    [average],
                    [bound],
                    [peak_time],
                    [final_residual],
                    [final_active_max],
                )
            )
            time_series_rows.extend(
                {
                    "weighting": weighting,
                    "weighting_label": WEIGHTING_LABELS[weighting],
                    "network": graph.name,
                    "t": float(time),
                    "E2": float(value),
                    "E2_std": 0.0,
                }
                for time, value in zip(times, curve, strict=True)
            )

        random_curves: list[np.ndarray] = []
        random_peaks: list[float] = []
        random_averages: list[float] = []
        random_bounds: list[float] = []
        random_peak_times: list[float] = []
        random_final_residuals: list[float] = []
        random_final_active_values: list[float] = []
        common_times: np.ndarray | None = None

        payloads = [(graph, weighting, parameters) for graph in base_random]
        max_workers = min(8, len(payloads), os.cpu_count() or 1)
        with ProcessPoolExecutor(max_workers=max_workers) as executor:
            random_simulations = list(executor.map(_simulate_weighted_graph, payloads))

        for graph, result in random_simulations:
            times = np.asarray(result["times"])
            curve = np.asarray(result["curve"])
            peak = float(result["peak"])
            average = float(result["average"])
            bound = float(result["bound"])
            peak_time = float(result["peak_time"])
            final_residual = float(result["final_residual"])
            final_active_max = float(result["final_active_max"])
            mass_error = float(result["maximum_mass_error"])
            minimum_state = float(result["minimum_state"])
            scenario_validation.append(
                (mass_error, minimum_state, final_residual, final_active_max)
            )

            common_times = times if common_times is None else common_times
            if not np.array_equal(times, common_times):
                raise RuntimeError("Residual trajectories do not share the common grid.")
            random_curves.append(curve)
            random_peaks.append(peak)
            random_averages.append(average)
            random_bounds.append(bound)
            random_peak_times.append(peak_time)
            random_final_residuals.append(final_residual)
            random_final_active_values.append(final_active_max)

            metrics = network_metrics(graph.adjacency)
            random_rows.append(
                {
                    "weighting": weighting,
                    "weighting_label": WEIGHTING_LABELS[weighting],
                    "network": graph.name,
                    "n": graph.n,
                    "realization": graph.realization,
                    "seed": graph.seed,
                    **metrics,
                    "row_sum_min": float(np.min(graph.adjacency.sum(axis=1))),
                    "row_sum_max": float(np.max(graph.adjacency.sum(axis=1))),
                    "initial_source_outgoing_channels": int(
                        np.count_nonzero(graph.adjacency[:, INITIAL_SOURCE_NODE])
                        - int(graph.adjacency[INITIAL_SOURCE_NODE, INITIAL_SOURCE_NODE] > 0.0)
                    ),
                    "E2_max": peak,
                    "E2_time_average": average,
                    "B2": bound,
                    "E2_max_over_B2": peak / bound,
                    "t_peak": peak_time,
                    "E2_final": final_residual,
                    "active_final_max": final_active_max,
                    "maximum_local_mass_error": mass_error,
                    "minimum_compartment_value": minimum_state,
                }
            )

        curves = np.vstack(random_curves)
        mean_curve = curves.mean(axis=0)
        std_curve = curves.std(axis=0, ddof=1)
        assert common_times is not None

        time_series_rows.extend(
            {
                "weighting": weighting,
                "weighting_label": WEIGHTING_LABELS[weighting],
                "network": "Sparse random",
                "t": float(time),
                "E2": float(mean),
                "E2_std": float(std),
            }
            for time, mean, std in zip(
                common_times,
                mean_curve,
                std_curve,
                strict=True,
            )
        )

        summary_rows.append(
            _summary_row(
                weighting,
                "Sparse random",
                random_peaks,
                random_averages,
                random_bounds,
                random_peak_times,
                random_final_residuals,
                random_final_active_values,
            )
        )

        validation_rows.append(
            {
                "weighting": weighting,
                "weighting_label": WEIGHTING_LABELS[weighting],
                "maximum_local_mass_error": max(item[0] for item in scenario_validation),
                "minimum_compartment_value": min(item[1] for item in scenario_validation),
                "maximum_final_residual": max(item[2] for item in scenario_validation),
                "maximum_final_active_fraction": max(item[3] for item in scenario_validation),
                "final_residual_tolerance": FINAL_RESIDUAL_TOLERANCE,
                "final_active_tolerance": FINAL_ACTIVE_TOLERANCE,
                "number_of_trajectories": len(scenario_validation),
            }
        )

    return (
        pd.DataFrame(summary_rows),
        pd.DataFrame(time_series_rows),
        pd.DataFrame(random_rows),
        pd.DataFrame(validation_rows),
    )


def build_cubic_cache(ensembles: RandomEnsembles) -> CubicCache:
    """Compute cubic metrics once for every sparse-random realization."""
    cache: CubicCache = {}
    for n, graphs in ensembles.items():
        for graph in graphs:
            assert graph.realization is not None
            cache[(n, graph.realization)] = cubic_dictionary_metrics(
                graph.adjacency
            )
    return cache


def cubic_dictionary_results(
    ensembles: RandomEnsembles,
    cache: CubicCache,
) -> pd.DataFrame:
    """Compute Table 4 and Figure 5 of the article."""
    rows: list[dict[str, float | int | str]] = []

    for n in NETWORK_SIZES:
        for graph in deterministic_graphs(n):
            rows.append(
                {
                    "network": graph.name,
                    "n": n,
                    "D_full_3": complete_cubic_dimension(n),
                    **cubic_dictionary_metrics(graph.adjacency),
                    "Phi2_dim_std": 0.0,
                    "Phi3_seed_dim_std": 0.0,
                    "Phi3_linear_saturation_additions_std": 0.0,
                    "Phi3_dim_std": 0.0,
                    "z3_edge_dim_std": 0.0,
                }
            )

        random_frame = pd.DataFrame(
            cache[(n, graph.realization)]
            for graph in ensembles[n]
            if graph.realization is not None
        )
        row: dict[str, float | int | str] = {
            "network": "Sparse random",
            "n": n,
            "D_full_3": complete_cubic_dimension(n),
        }
        for column in (
            "Phi2_dim",
            "Phi3_seed_dim",
            "Phi3_linear_saturation_additions",
            "Phi3_dim",
            "z3_edge_dim",
        ):
            mean, std = mean_and_sample_std(random_frame[column])
            row[column] = mean
            row[f"{column}_std"] = std
        rows.append(row)

    return pd.DataFrame(rows)


def random_realization_results(
    ensembles: RandomEnsembles,
    cache: CubicCache,
) -> pd.DataFrame:
    """Store realization seeds and raw graph/dictionary quantities."""
    rows: list[dict[str, float | int | None]] = []
    for n, graphs in ensembles.items():
        for graph in graphs:
            assert graph.realization is not None
            rows.append(
                {
                    "n": n,
                    "realization": graph.realization,
                    "seed": graph.seed,
                    **network_metrics(graph.adjacency),
                    "D_edge_2": edge_quadratic_dimension(graph.adjacency),
                    **{
                        key: value
                        for key, value in cache[(n, graph.realization)].items()
                        if key
                        in {
                            "Phi3_seed_dim",
                            "Phi3_linear_saturation_additions",
                            "Phi3_dim",
                        }
                    },
                }
            )
    return pd.DataFrame(rows)


def write_structural_outputs(ensembles: RandomEnsembles) -> None:
    """Write support-dependent dimensions and raw structural realizations."""
    quadratic_dimension_results(ensembles).to_csv(
        DATA_DIR / "dimension_comparison.csv", index=False
    )
    network_quantity_results(ensembles).to_csv(
        DATA_DIR / "network_quantities.csv", index=False
    )
    cubic_cache = build_cubic_cache(ensembles)
    cubic_dictionary_results(ensembles, cubic_cache).to_csv(
        DATA_DIR / "cubic_dictionary_size.csv", index=False
    )
    random_realization_results(ensembles, cubic_cache).to_csv(
        DATA_DIR / "sparse_random_realizations.csv", index=False
    )


def write_dynamic_outputs(ensembles: RandomEnsembles) -> None:
    """Write trajectories and residuals for both weighting configurations."""
    residual_summary, residual_curves, random_residuals, validation = residual_results(
        ensembles
    )
    residual_summary.to_csv(
        DATA_DIR / "residual_sensitivity_summary.csv", index=False
    )
    residual_curves.to_csv(
        DATA_DIR / "residual_sensitivity_timeseries.csv", index=False
    )
    random_residuals.to_csv(
        DATA_DIR / "sparse_random_residual_realizations.csv", index=False
    )
    validation.to_csv(DATA_DIR / "simulation_validation.csv", index=False)

    unit_summary = residual_summary[
        residual_summary["weighting"] == UNIT_WEIGHTING
    ].drop(columns=["weighting", "weighting_label"])
    unit_curves = residual_curves[
        residual_curves["weighting"] == UNIT_WEIGHTING
    ].drop(columns=["weighting", "weighting_label"])
    unit_summary.to_csv(DATA_DIR / "residual_summary.csv", index=False)
    unit_curves.to_csv(DATA_DIR / "residual_timeseries.csv", index=False)


def main(stage: str = "all") -> None:
    """Generate all outputs, or only the structural or dynamic subset."""
    if stage not in {"all", "structural", "dynamic"}:
        raise ValueError("stage must be 'all', 'structural', or 'dynamic'.")

    import gc

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    ensembles = build_random_ensembles()

    if stage in {"all", "structural"}:
        write_structural_outputs(ensembles)
        gc.collect()

    if stage in {"all", "dynamic"}:
        write_dynamic_outputs(ensembles)
        gc.collect()

    print(f"Data written to {DATA_DIR} ({stage} stage)")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--stage",
        choices=("all", "structural", "dynamic"),
        default="all",
        help="Generate all outputs or only one experiment subset.",
    )
    arguments = parser.parse_args()
    main(arguments.stage)
