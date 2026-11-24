"""Fast checks for the published and revised experimental contracts.

These tests read the files shipped with the release. The independent, complete
rebuild is performed by scripts/reproduce_all.py and then checked again by CI.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from graph_topologies import path_graph, normalize_incoming_transmission_intensity
from lifting_metrics import cubic_dictionary_metrics


def test_original_higher_order_corridor_counts() -> None:
    """The reproduced n=100 path and star counts must match the paper."""
    counts = pd.read_csv(ROOT / "output/data/cubic_dictionary_size.csv")
    for network, expected in (("Path", 4458), ("Star", 42482)):
        case = counts[(counts.network == network) & (counts.n == 100)]
        assert len(case) == 1
        assert int(case.iloc[0].z3_edge_dim) == expected


def test_peak_grid_is_rebuilt_and_agrees_with_published_fixture() -> None:
    """The reference is used for testing, not for generating grid peaks."""
    baseline = pd.read_csv(ROOT / "experiments/reference/peak_grid_sensitivity_v1.0.2.csv")
    current = pd.read_csv(ROOT / "output/data/peak_grid_sensitivity.csv")
    assert len(current) == len(baseline) == 10
    assert list(current[["network", "weighting"]].itertuples(index=False, name=None)) == list(
        baseline[["network", "weighting"]].itertuples(index=False, name=None)
    )
    assert np.allclose(current.coarse_peak, baseline.coarse_peak, rtol=0, atol=1e-9)
    assert np.allclose(current.fine_peak, baseline.fine_peak, rtol=0, atol=1e-9)


def test_complete_symmetric_dimensions() -> None:
    """For 100 nodes the full symmetric basis counts are exact integers."""
    frame = pd.read_csv(ROOT / "experiments/data/structural_benchmarks.csv")
    cases = frame[frame.n == 100]
    assert len(cases) == 3
    assert set(cases.symmetric_d2) == {80600}
    assert set(cases.symmetric_d3) == {10827400}


def test_revised_residual_bounds_hold_per_realization() -> None:
    """Do not compare a peak mean against a bound mean as a substitute."""
    frame = pd.read_csv(ROOT / "experiments/data/refined_bounds_by_realization.csv")
    assert len(frame) == 104
    assert (frame.E2_max <= frame.new_refined_bound + 1e-9).all()
    assert (frame.new_refined_bound <= frame.original_bound + 1e-9).all()


def test_initial_node_sensitivity_is_not_a_topology_ranking() -> None:
    """Check the eight controlled seeding experiments and numerical norms."""
    frame = pd.read_csv(ROOT / "experiments/data/source_node_sensitivity.csv")
    assert len(frame) == 8
    assert frame.E2_infty_max.gt(0).all()
    assert np.allclose(frame.E2_RMS_max, frame.E2_max / np.sqrt(2 * frame.m))


def test_normalization_retains_dictionary_support() -> None:
    """Changing incoming intensity must not change the observable dictionary."""
    original = path_graph(12)
    normalized = normalize_incoming_transmission_intensity(original, 1.0)
    assert np.array_equal(original.adjacency > 0, normalized.adjacency > 0)
    assert cubic_dictionary_metrics(original.adjacency) == cubic_dictionary_metrics(normalized.adjacency)


def test_all_generated_review_artifacts_are_present() -> None:
    """Every table and figure cited in the revision guide is reproducible."""
    data = ROOT / "experiments/data"
    for filename in (
        "structural_benchmarks.csv", "refined_bounds_by_realization.csv",
        "refined_residual_summary.csv", "source_node_sensitivity.csv",
        "random_normalized_rms.csv", "sparse_operator_costs.csv",
        "dictionary_build_runs.csv", "large_networks.csv",
        "peak_grid_refinement_check.csv",
    ):
        assert (data / filename).is_file(), filename
    for filename in (
        "symmetric_benchmarks.tex", "refined_residuals.tex", "initial_node_sensitivity.tex"
    ):
        assert (ROOT / "experiments/tables" / filename).is_file()
    assert (ROOT / "experiments/figures/figure_2_dimension_comparison.pdf").is_file()
