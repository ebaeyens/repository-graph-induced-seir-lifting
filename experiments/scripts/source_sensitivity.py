"""Independent extended-numerics source-location and residual-normalization experiment.
Uses unmodified Zenodo 1.0.2 model/graph functions, adds analysis external to release.
"""
from __future__ import annotations
import argparse, sys
from pathlib import Path
import numpy as np, pandas as pd

def residual_coordinates(traj, adj, beta):
    """Compute the infection and exposure coordinates of the first closure residual for all time samples, retaining their signs."""
    n = len(adj)
    recv, src = np.nonzero(adj)
    s = traj[:n]
    e = traj[n:2 * n]
    i = traj[2 * n:3 * n]
    h = adj @ i
    r_si = -beta * s[recv] * i[src] * h[recv]
    r_se = -beta * s[recv] * e[src] * h[recv] + beta * s[recv] * s[src] * h[src]
    return (r_si, r_se)

def main(repo: Path, out: Path, randomout: Path):
    """Move the localized initial infection while holding its mass and all solver settings fixed; record Euclidean, infinity, and per-coordinate RMS residuals."""
    sys.path.insert(0, str(repo / 'scripts'))
    from seir_network import SEIRParameters, simulate_seir, localized_initial_condition
    from residuals import residual_time_series, time_average, first_grid_peak
    from graph_topologies import path_graph, star_graph, normalize_incoming_transmission_intensity
    # All seed positions use the same initial exposed/infectious mass.
    params = SEIRParameters()
    n = 100
    records = []
    for topo, graph in [('Path', path_graph(n)), ('Star', star_graph(n))]:
        for source, label in [(0, 'end' if topo == 'Path' else 'hub'), (49 if topo == 'Path' else 99, 'middle' if topo == 'Path' else 'leaf')]:
            state = localized_initial_condition(n)
            if source != 0:
                state[source] = 1.0 - 0.002
                state[0] = 1.0
                state[n] = 0.0
                state[2 * n] = 0.0
                state[n + source] = 0.001
                state[2 * n + source] = 0.001
            assert np.max(np.abs(state[:n] + state[n:2 * n] + state[2 * n:3 * n] + state[3 * n:] - 1)) < 1e-15
            for weight in ['unit', 'fixed_incoming_transmission_intensity']:
                g = graph if weight == 'unit' else normalize_incoming_transmission_intensity(graph, 1.0)
                sol = simulate_seir(g.adjacency, params, state, 480.0, 3201)
                values = residual_time_series(sol.y, g.adjacency, params)
                rsi, rse = residual_coordinates(sol.y, g.adjacency, params.beta)
                independent = np.sqrt(np.sum(rsi * rsi + rse * rse, axis=0))
                assert np.max(abs(values - independent)) < 1e-12
                infseries = np.maximum(np.max(abs(rsi), axis=0), np.max(abs(rse), axis=0))
                m = int(np.count_nonzero(g.adjacency))
                root = float(np.sqrt(2 * m))
                p, t = first_grid_peak(sol.t, values)
                records.append(dict(network=topo, weighting=weight, initial_node_one_based=source + 1, initial_position=label, n=n, m=m, E2_max=p, t_peak=t, E2_time_average=time_average(sol.t, values), E2_RMS_max=p / root, E2_RMS_time_average=time_average(sol.t, values) / root, E2_infty_max=float(infseries.max()), E2_infty_t_peak=float(sol.t[infseries.argmax()]), max_local_mass_error=float(np.max(abs(sol.y[:n] + sol.y[n:2 * n] + sol.y[2 * n:3 * n] + sol.y[3 * n:] - 1))), min_compartment_value=float(sol.y.min()), E2_final=float(values[-1])))
    df = pd.DataFrame(records)
    out.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out, index=False)
    original = pd.read_csv(repo / 'output/data/residual_sensitivity_summary.csv')
    for topo in ['Path', 'Star']:
        for weight in ['unit', 'fixed_incoming_transmission_intensity']:
            old = original[(original.network == topo) & (original.weighting == weight)].iloc[0].E2_max
            new = df[(df.network == topo) & (df.weighting == weight) & (df.initial_node_one_based == 1)].iloc[0].E2_max
            assert abs(old - new) < 1e-11, (topo, weight, old, new)
    # Normalize per realization before computing ensemble means and SDs.
    raw = pd.read_csv(repo / 'output/data/sparse_random_residual_realizations.csv')
    raw['E2_RMS_max'] = raw['E2_max'] / np.sqrt(2 * raw['m'])
    raw['E2_RMS_time_average'] = raw['E2_time_average'] / np.sqrt(2 * raw['m'])
    stats = raw.groupby('weighting').agg({'E2_RMS_max': ['mean', 'std'], 'E2_RMS_time_average': ['mean', 'std']})
    stats.columns = ['_'.join(c) for c in stats.columns]
    stats.reset_index().to_csv(randomout, index=False)
    print(df[['network', 'weighting', 'initial_position', 'E2_max', 't_peak', 'E2_infty_max', 'E2_RMS_max']].to_string(index=False, float_format=lambda f: f'{f:.6g}'))
    print('\nRandom normalized stats:\n', stats)
if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--repo', required=True, type=Path)
    p.add_argument('--out', required=True, type=Path)
    p.add_argument('--randomout', required=True, type=Path)
    a = p.parse_args()
    main(a.repo, a.out, a.randomout)
