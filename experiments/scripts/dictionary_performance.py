"""Measure original 1.0.2 cubic dictionary construction in separate Python processes.
OS peak RSS includes runtime imports and is an approximate resource measurement.
Not an estimate of full lifted operator assembly, integration or general Carleman baselines.
"""
from __future__ import annotations
import argparse, json, os, resource, statistics, subprocess, sys, time
from pathlib import Path


def maxrss_mib(value: float) -> float:
    """Convert OS peak RSS to MiB (macOS reports bytes, Linux reports KiB)."""
    return value / (1024 * 1024) if sys.platform == "darwin" else value / 1024
import pandas as pd

def single(args):
    """Measure one isolated dictionary construction, reporting elapsed time and process peak RSS as approximate machine-dependent costs."""
    sys.path.insert(0, str(args.repo / 'scripts'))
    from graph_topologies import path_graph, star_graph, sparse_random_graph
    from lifting_metrics import cubic_dictionary_metrics
    if args.topo == 'Path':
        graph = path_graph(args.n)
    elif args.topo == 'Star':
        graph = star_graph(args.n)
    else:
        graph = sparse_random_graph(args.n, 4.0, 1.0, 1.0, seed=12345 + args.n, realization=0)
    before = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    t0 = time.perf_counter()
    metrics = cubic_dictionary_metrics(graph.adjacency)
    elapsed = time.perf_counter() - t0
    after = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    print(json.dumps(dict(network=args.topo, n=args.n, elapsed_s=elapsed, base_peak_rss_mib=maxrss_mib(before), peak_rss_mib=maxrss_mib(after), incremental_peak_rss_mib=maxrss_mib(max(0, after - before)), phi2_dim=metrics['Phi2_dim'], phi3_dim=metrics['Phi3_dim'], z3_dim=metrics['z3_edge_dim'])))

def allcases(args):
    """Execute repeated measurements in separate interpreter processes so large dictionaries do not accumulate across trials."""
    cases = [('Path', 25), ('Star', 25), ('Sparse random', 25), ('Path', 50), ('Star', 50), ('Sparse random', 50), ('Path', 100), ('Star', 100), ('Sparse random', 100), ('Path', 200), ('Star', 200), ('Sparse random', 200), ('Path', 500), ('Sparse random', 500)]
    rows = []
    # Isolate repetitions to avoid sharing the Python heap across trials.
    for topo, n in cases:
        for rep in range(3):
            cmd = [sys.executable, __file__, '--single', '--repo', str(args.repo), '--topo', topo, '--n', str(n)]
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            obs = json.loads(result.stdout.strip().splitlines()[-1])
            obs['repetition'] = rep + 1
            rows.append(obs)
        print('completed', topo, n, flush=True)
    df = pd.DataFrame(rows)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(args.out, index=False)
    grp = df.groupby(['network', 'n']).agg({'elapsed_s': 'median', 'peak_rss_mib': 'median', 'incremental_peak_rss_mib': 'median', 'z3_dim': 'first'}).reset_index()
    grp.to_csv(args.out.with_name('dictionary_build_summary.csv'), index=False)
    print(grp.to_string(index=False, float_format=lambda v: f'{v:.3f}'))
if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--single', action='store_true')
    p.add_argument('--repo', required=True, type=Path)
    p.add_argument('--out', type=Path)
    p.add_argument('--topo', type=str)
    p.add_argument('--n', type=int)
    a = p.parse_args()
    if a.single:
        single(a)
    else:
        allcases(a)
