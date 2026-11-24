"""Finite-range, larger synthetic graph experiments using release 1.0.2 functions.
These experiments do not test asymptotic uniform-degree assumptions.
"""
from __future__ import annotations
import argparse, sys, time
from pathlib import Path
import numpy as np, pandas as pd

def main(repo: Path, out: Path):
    """Generate path and sparse directed random supports at 1,000 and 2,000 nodes, then count their linearly closed cubic dictionaries. These are finite-range synthetic examples."""
    sys.path.insert(0, str(repo / 'scripts'))
    from graph_topologies import path_graph, sparse_random_ensemble
    from lifting_metrics import cubic_dictionary_metrics, network_metrics
    rows = []
    for n in [1000, 2000]:
        tic = time.perf_counter()
        g = path_graph(n)
        stats = cubic_dictionary_metrics(g.adjacency)
        rows.append(dict(network='Path', realization=0, seed='', **network_metrics(g.adjacency), **stats, elapsed_s=time.perf_counter() - tic))
        print('Path', n, stats['z3_edge_dim'], flush=True)
        ens = sparse_random_ensemble(n=n, realizations=10, mean_degree=4.0, off_diagonal_weight=1.0, diagonal_weight=1.0, seed=12345 + n, initial_source_node=0, require_initial_source_outgoing_channel=True)
        for k, g in enumerate(ens):
            tic = time.perf_counter()
            stats = cubic_dictionary_metrics(g.adjacency)
            rows.append(dict(network='Sparse random', realization=k, seed=g.seed, **network_metrics(g.adjacency), **stats, elapsed_s=time.perf_counter() - tic))
        print('Sparse random', n, 10, flush=True)
    df = pd.DataFrame(rows)
    out.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out, index=False)
    agg = df.groupby(['network', 'n']).agg({'m': ['mean', 'std'], 'Delta_in': ['mean', 'std'], 'Phi2_dim': ['mean', 'std'], 'Phi3_dim': ['mean', 'std'], 'z3_edge_dim': ['mean', 'std'], 'elapsed_s': ['mean', 'std']})
    agg.columns = ['_'.join(map(str, t)) for t in agg.columns]
    agg.reset_index().to_csv(out.with_name('large_networks_summary.csv'), index=False)
    print(agg.to_string())
if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--repo', required=True, type=Path)
    p.add_argument('--out', required=True, type=Path)
    a = p.parse_args()
    main(a.repo, a.out)
