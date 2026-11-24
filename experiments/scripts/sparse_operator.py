"""Independent sparse K_d assembly for SEIR graph-induced monomial dictionaries.
Not published with release 1.0.2. It is for experimental verification only.
The algorithm uses explicit polynomial differentiation and coefficient aggregation.
"""
from __future__ import annotations
import argparse, json, os, resource, sys, time
from collections import defaultdict
from pathlib import Path


def maxrss_mib(value: float) -> float:
    """Convert OS peak RSS to MiB (macOS reports bytes, Linux reports KiB)."""
    return value / (1024 * 1024) if sys.platform == "darwin" else value / 1024
import numpy as np
from scipy.sparse import coo_matrix

def assemble(adj, beta=0.8, sigma=0.25, gamma=0.1, d=3):
    """Assemble the sparse, truncated linear generator K_d from the graph-supported monomial basis. Differentiate each scalar observable and combine coefficients of identical monomials."""
    from lifting_metrics import quadratic_dictionary, linear_saturation, quadratic_successors, incoming_sources, canonical_monomial
    n = adj.shape[0]
    deg1 = [((c, i),) for c in ['S', 'E', 'I', 'R'] for i in range(n)]
    deg2 = sorted(quadratic_dictionary(adj))
    deg3 = []
    if d >= 3:
        sources = incoming_sources(adj)
        seeds = set()
        for q in deg2:
            seeds.update(quadratic_successors(q, sources))
        deg3 = sorted(linear_saturation(seeds))
    basis = deg1 + deg2 + deg3
    pos = {q: i for i, q in enumerate(basis)}
    assert len(pos) == len(basis)
    rows = []
    cols = []
    vals = []
    # The polynomial derivative is assembled row by row in the basis.
    for row, q in enumerate(basis):
        k = len(q)
        pol = defaultdict(float)
        for ind, (c, node) in enumerate(q):
            rest = q[:ind] + q[ind + 1:]
            if c == 'E':
                pol[q] += -sigma
            elif c == 'I':
                pol[q] += -gamma
                pol[canonical_monomial((*rest, ('E', node)))] += sigma
            elif c == 'R':
                pol[canonical_monomial((*rest, ('I', node)))] += gamma
            if k < d and c in ('S', 'E'):
                sign = -1 if c == 'S' else 1
                for source in np.flatnonzero(adj[node]):
                    term = canonical_monomial((*rest, ('S', node), ('I', int(source))))
                    pol[term] += sign * beta * float(adj[node, source])
        for q1, coef in pol.items():
            if abs(coef) > 1e-13:
                if q1 not in pos:
                    raise AssertionError(f'unclosed monomial degree {k}: {q1}')
                rows.append(row)
                cols.append(pos[q1])
                vals.append(coef)
    K = coo_matrix((vals, (rows, cols)), shape=(len(basis), len(basis))).tocsr()
    K.sum_duplicates()
    K.eliminate_zeros()
    return (K, basis, (len(deg1), len(deg2), len(deg3)))

def eval_z(x, basis, n):
    """Evaluate the retained commutative monomial basis at one SEIR state."""
    blocks = {'S': x[:n], 'E': x[n:2 * n], 'I': x[2 * n:3 * n], 'R': x[3 * n:]}
    return np.array([np.prod([blocks[c][node] for c, node in q]) for q in basis])

def eval_dz(x, dx, basis, n):
    """Apply the product rule directly to obtain the true derivative of each retained observable, including the omitted truncation forcing."""
    blocks = {'S': x[:n], 'E': x[n:2 * n], 'I': x[2 * n:3 * n], 'R': x[3 * n:]}
    deriv = {'S': dx[:n], 'E': dx[n:2 * n], 'I': dx[2 * n:3 * n], 'R': dx[3 * n:]}
    out = []
    for q in basis:
        total = 0.0
        for i, (c, node) in enumerate(q):
            factors = [blocks[cc][nn] for j, (cc, nn) in enumerate(q) if j != i]
            total += deriv[c][node] * np.prod(factors)
        out.append(total)
    return np.array(out)

def validate(repo):
    """Compare the assembled operator with the exact nonlinear derivatives on small admissible random states, including the quadratic truncation residual."""
    sys.path.insert(0, str(repo / 'scripts'))
    from graph_topologies import path_graph, star_graph
    from seir_network import seir_rhs, SEIRParameters
    from residuals import residual_time_series
    rng = np.random.default_rng(93214)
    for n in [2, 3, 5]:
        for graph in [path_graph(n), star_graph(n)]:
            for d in [2, 3]:
                K, basis, dims = assemble(graph.adjacency, d=d)
                for rep in range(10):
                    x = rng.dirichlet(np.array([1.5, 1.2, 0.9, 1.0]), size=n).T.reshape(-1)
                    dx = seir_rhs(0, x, graph.adjacency, SEIRParameters())
                    dz = eval_dz(x, dx, basis, n)
                    model = K @ eval_z(x, basis, n)
                    offset = dims[0] + (dims[1] if d == 3 else 0)
                    assert np.max(abs(dz[:offset] - model[:offset])) < 2e-13, (n, d, rep, 'retained mismatch')
                    if d == 2:
                        original_residual = float(residual_time_series(x[:, None], graph.adjacency, SEIRParameters())[0])
                        independently_assembled_residual = float(np.linalg.norm(dz[offset:] - model[offset:]))
                        assert abs(original_residual - independently_assembled_residual) < 3e-13, (n, d, rep, 'residual mismatch')
                    assert np.isfinite(dz).all()
                print('VALIDATED', n, graph.name, d, 'dim', len(basis), 'NNZ', K.nnz, flush=True)

def main(args):
    """Benchmark sparse operator assembly on specified synthetic supports and report dimensions, nonzeros, CSR storage, time and peak memory."""
    sys.path.insert(0, str(args.repo / 'scripts'))
    from graph_topologies import path_graph, star_graph, sparse_random_graph
    validate(args.repo)
    rows = []
    for n in [25, 50, 100]:
        for graph in [path_graph(n), star_graph(n), sparse_random_graph(n, 4.0, 1.0, 1.0, seed=12345 + n, realization=0)]:
            for d in [2, 3]:
                baseline = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
                tic = time.perf_counter()
                K, basis, dims = assemble(graph.adjacency, d=d)
                elapsed = time.perf_counter() - tic
                peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
                rows.append(dict(n=n, network=graph.name, degree=d, dimension=K.shape[0], nnz=K.nnz, density=K.nnz / K.shape[0] ** 2, CSR_storage_bytes=K.data.nbytes + K.indices.nbytes + K.indptr.nbytes, elapsed_s=elapsed, process_peak_RSS_MiB=maxrss_mib(peak), peak_since_previous_MiB=maxrss_mib(max(0, peak - baseline))))
                print('ASSEMBLED', n, graph.name, d, K.shape[0], K.nnz, round(elapsed, 3), flush=True)
    import pandas as pd
    df = pd.DataFrame(rows)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(args.out, index=False)
if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--repo', required=True, type=Path)
    p.add_argument('--out', required=True, type=Path)
    a = p.parse_args()
    main(a)
