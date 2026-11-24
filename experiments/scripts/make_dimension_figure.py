"""Reproducible Figure 2 replacement from archived and verified extended-numerics CSV."""
import argparse
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.ticker import LogLocator, NullFormatter

def main(source: Path, out: Path):
    """Plot complete ordered, complete symmetric, and graph-induced dimensions from the independently regenerated structural benchmark CSV."""
    df = pd.read_csv(source)
    d = df[df.network == 'Path'].sort_values('n')
    sr = df[df.network == 'Sparse random'].sort_values('n')
    f, ax = plt.subplots(figsize=(7.0, 4.0))
    ax.loglog(d.n, d.ordered_d2, marker='s', linewidth=1.75, color='#6b7280', label='Complete ordered')
    ax.loglog(d.n, d.symmetric_d2, marker='D', linewidth=1.75, ls='--', color='#a3483e', label='Complete symmetric')
    ax.loglog(d.n, d.graph_d2, marker='o', linewidth=1.75, color='#225f97', label='Graph-induced: path/star')
    ax.errorbar(sr.n, sr.graph_d2, yerr=sr.graph_d2_std, fmt='^-', linewidth=1.75, color='#23835d', capsize=2, label='Graph-induced: sparse random')
    ax.set_xticks([25, 50, 100, 200, 500])
    ax.set_xticklabels(['25', '50', '100', '200', '500'])
    ax.set_xlabel('Number of nodes, $n$')
    ax.set_ylabel('Cumulative dimension through degree 2')
    ax.grid(True, alpha=0.18, which='both', linewidth=0.6)
    ax.set_xlim(22, 550)
    ax.set_ylim(150, 6000000.0)
    ax.legend(loc='upper left', fontsize=8, frameon=True, framealpha=0.96)
    f.tight_layout()
    out.parent.mkdir(parents=True, exist_ok=True)
    f.savefig(out, format='pdf', bbox_inches='tight')
    plt.close(f)
if __name__ == '__main__':
    a = argparse.ArgumentParser()
    a.add_argument('--source', type=Path, required=True)
    a.add_argument('--out', type=Path, required=True)
    args = a.parse_args()
    main(args.source, args.out)
