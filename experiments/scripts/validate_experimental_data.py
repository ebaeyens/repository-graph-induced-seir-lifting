"""Validate supplementary numerical results against the archived reference data."""
from __future__ import annotations
import argparse, math
from pathlib import Path
import numpy as np, pandas as pd

def main(repo: Path, results: Path):
    """Check that the numeric outputs needed by the revised manuscript are present and that their structural identities and residual inequalities hold."""
    main2 = pd.read_csv(results / 'structural_benchmarks.csv')
    cases = main2[main2.n.eq(100)]
    assert set(cases.network) == {'Path', 'Star', 'Sparse random'}
    for _, r in cases.iterrows():
        assert int(r.symmetric_d2) == 80600 and int(r.symmetric_d3) == 10827400
        assert int(r.ordered_d2) == 160400 and int(r.ordered_d3) == 64160400
        assert np.isclose(r.reachable_support_monomial_d3, r.graph_d3)
    bounds = pd.read_csv(results / 'refined_residual_summary.csv')
    assert len(bounds) == 6
    assert (bounds.E2_peak_mean < bounds.B_refined_mean).all()
    assert (bounds.B_refined_mean < bounds.B_original_mean).all()
    realization = pd.read_csv(results / 'refined_bounds_by_realization.csv')
    assert len(realization) == 104
    assert (realization.E2_max <= realization.new_refined_bound + 1e-10).all()
    assert realization.new_ratio.max() < 0.052
    ss = pd.read_csv(results / 'source_node_sensitivity.csv')
    assert len(ss) == 8
    assert set(ss.initial_node_one_based) == {1, 50, 100}
    big = pd.read_csv(results / 'large_networks.csv')
    assert len(big) == 22 and set(big.n) == {1000, 2000}
    op = pd.read_csv(results / 'sparse_operator_costs.csv')
    assert len(op) == 18 and (op.nnz > 0).all()
    k = op.query('n==100 and degree==3')
    assert len(k) == 3
    assert set(k.nnz) == {10494, 105554, 29345}
    assert (repo / 'output/data/sparse_random_realizations.csv').exists()
    assert (repo / 'output/data/peak_grid_sensitivity.csv').exists()
    print('EXPERIMENTAL_DATA_PASS; structural, residual, seed, large-network and operator CSVs')
if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--repo', required=True, type=Path)
    p.add_argument('--results', required=True, type=Path)
    a = p.parse_args()
    main(a.repo, a.results)
