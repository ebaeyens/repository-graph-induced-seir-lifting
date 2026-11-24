"""Compute rigorous approved the proved residual estimates/R1 p=1 bounds for original 1.0.2 networks.
Does not modify 1.0.2 outputs. Peak values are from the original archived CSV.
"""
from __future__ import annotations
import argparse, sys
from pathlib import Path
import numpy as np, pandas as pd

def refined_r1(a, beta=0.8, p=1.0):
    """Compute the refined analytical Euclidean residual bound using each channel and its two receiving-node infection pressures. The inner scalar maximization accounts for local susceptible depletion."""
    a = np.asarray(a)
    n = len(a)
    recv, src = np.nonzero(a)
    if len(recv) == 0:
        return 0.0
    d = a.sum(axis=1)

    # Maximize the susceptible factor on 0 <= I_i <= p.
    def B(k, i):
        c = a[k, i]
        b = d[k] - c
        if c == 0:
            return p * d[k]
        u = min(p, max(0.0, (c - b * p) / (2 * c)))
        return (1 - u) * (b * p + c * u)
    D = np.fromiter((max(B(i, i), B(j, i)) for i, j in zip(recv, src, strict=True)), dtype=float, count=len(recv))
    return float(beta * np.linalg.norm(D))

def main(repo: Path, out: Path, rawout: Path):
    """Recreate each accepted graph and both weightings, then compare observed peaks with old, uniform, and refined analytic bounds. Average realization-wise ratios only after calculating them individually."""
    sys.path.insert(0, str(repo / 'scripts'))
    from graph_topologies import path_graph, star_graph, sparse_random_ensemble, normalize_incoming_transmission_intensity
    from residuals import residual_bound
    from seir_network import SEIRParameters
    params = SEIRParameters()
    n = 100
    # Reuse the exact accepted random graph seed stream from the baseline.
    ensemble = sparse_random_ensemble(n, 50, 4.0, 1.0, 1.0, seed=12345 + n, initial_source_node=0, require_initial_source_outgoing_channel=True)
    graphs = [path_graph(n), star_graph(n), *ensemble]
    original = pd.read_csv(repo / 'output/data/sparse_random_residual_realizations.csv')
    summaries = pd.read_csv(repo / 'output/data/residual_sensitivity_summary.csv')
    raw = []
    for weighting in ['unit', 'fixed_incoming_transmission_intensity']:
        for k, g in enumerate(graphs):
            graph = g if weighting == 'unit' else normalize_incoming_transmission_intensity(g, 1.0)
            a = graph.adjacency
            m = np.count_nonzero(a)
            delta = np.max(a.sum(axis=1))
            B0 = residual_bound(a, params)
            B_uniform = np.sqrt(m) * params.beta * delta
            B_refined = refined_r1(a)
            assert B_refined <= B_uniform + 1e-10 and B_uniform <= B0 + 1e-10
            if g.name != 'Sparse random':
                obs = summaries[(summaries.network == g.name) & (summaries.weighting == weighting)].iloc[0]
            else:
                obs = original[(original.network == 'Sparse random') & (original.weighting == weighting) & (original.seed == g.seed)].iloc[0]
            assert abs(B0 - obs.B2) < 1e-10, (weighting, g.name, g.seed, B0, obs.B2)
            raw.append(dict(network=g.name, weighting=weighting, realization=g.realization if g.realization is not None else -1, seed=g.seed if g.seed is not None else -1, n=n, m=m, delta_max=delta, original_bound=B0, new_uniform_bound=B_uniform, new_refined_bound=B_refined, E2_max=obs.E2_max, old_ratio=obs.E2_max / B0, new_ratio=obs.E2_max / B_refined))
    rawdf = pd.DataFrame(raw)
    rawout.parent.mkdir(parents=True, exist_ok=True)
    rawdf.to_csv(rawout, index=False)
    rows = []
    for (network, weight), grp in rawdf.groupby(['network', 'weighting']):
        std = lambda x: float(np.std(x, ddof=1)) if len(x) > 1 else 0.0
        rows.append(dict(network=network, weighting=weight, N=len(grp), E2_peak_mean=float(grp.E2_max.mean()), E2_peak_sd=std(grp.E2_max), B_original_mean=float(grp.original_bound.mean()), B_original_sd=std(grp.original_bound), B_uniform_mean=float(grp.new_uniform_bound.mean()), B_uniform_sd=std(grp.new_uniform_bound), B_refined_mean=float(grp.new_refined_bound.mean()), B_refined_sd=std(grp.new_refined_bound), ratio_new_mean=float(grp.new_ratio.mean()), ratio_new_sd=std(grp.new_ratio)))
    result = pd.DataFrame(rows)
    result.to_csv(out, index=False)
    print(result[['network', 'weighting', 'B_original_mean', 'B_refined_mean', 'ratio_new_mean']].to_string(index=False, float_format=lambda x: f'{x:.5f}'))
if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--repo', required=True, type=Path)
    p.add_argument('--out', required=True, type=Path)
    p.add_argument('--rawout', required=True, type=Path)
    a = p.parse_args()
    main(a.repo, a.out, a.rawout)
