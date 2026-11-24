"""extended-numerics independently derived full ordered/symmetric benchmarks from release 1.0.2 CSV.
Not part of the original Zenodo release. Run from the repository root.
"""
import argparse
from math import comb
from pathlib import Path
import pandas as pd

def main():
    """Read the original dimension results and add the exact combinatorial dimensions of ordered and symmetric full Carleman bases. The reachable-support count equals the graph-induced count under the proved SEIR equivalence."""
    parser = argparse.ArgumentParser()
    parser.add_argument('--repo', required=True, type=Path)
    parser.add_argument('--out', required=True, type=Path)
    args = parser.parse_args()
    source = args.repo / 'output/data/cubic_dictionary_size.csv'
    frame = pd.read_csv(source)
    results = []
    for r in frame.itertuples(index=False):
        n = int(r.n)
        N = 4 * n
        ordered2 = N + N ** 2
        ordered3 = ordered2 + N ** 3
        # Commutativity removes permutations from the full tensor basis.
        symmetric2 = N + comb(N + 1, 2)
        symmetric3 = symmetric2 + comb(N + 2, 3)
        d2 = N + float(r.Phi2_dim)
        d3 = float(r.z3_edge_dim)
        assert ordered3 == int(r.D_full_3)
        results.append(dict(network=r.network, n=n, ordered_d2=ordered2, symmetric_d2=symmetric2, graph_d2=d2, graph_d2_std=2 * pd.read_csv(args.repo / 'output/data/dimension_comparison.csv').query('network == @r.network and n == @n').iloc[0]['m_std'] if r.network == 'Sparse random' else 0.0, ordered_d3=ordered3, symmetric_d3=symmetric3, graph_d3=d3, graph_d3_std=float(r.z3_edge_dim_std), ordered_to_graph_d2=ordered2 / d2, symmetric_to_graph_d2=symmetric2 / d2, ordered_to_graph_d3=ordered3 / d3, symmetric_to_graph_d3=symmetric3 / d3, reachable_support_monomial_d2=d2, reachable_support_monomial_d3=d3, reachable_equivalence='established_by_support_equivalence_proof'))
    out = args.out
    out.parent.mkdir(parents=True, exist_ok=True)
    df = pd.DataFrame(results)
    df.to_csv(out, index=False)
    print('CREATED', out, 'ROWS', len(df))
    print(df[df.n == 100][['network', 'graph_d2', 'symmetric_d2', 'graph_d3', 'symmetric_d3', 'symmetric_to_graph_d3']].to_string(index=False, float_format=lambda x: f'{x:.3f}'))
if __name__ == '__main__':
    main()
