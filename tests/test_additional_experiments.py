"""additional regression and reproducibility checks (no external downloads)."""
from __future__ import annotations
import csv,sys,json
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'scripts'),str(ROOT/'experiments/scripts')]
from graph_topologies import path_graph,star_graph
from carleman_operators import split_dictionary,reachable_dictionary,symmetric_dictionary,assemble_shared
from sociopatterns_workplace import read_contact_records, aggregate_network, matched_graph, DATA_SHA256

def test_same_reachable_operator():
    for graph in (path_graph(4),star_graph(4)):
        A=graph.adjacency
        a=split_dictionary(A,3,ROOT);b=reachable_dictionary(A,3,ROOT)
        assert a==b
        Ka=assemble_shared(A,a,3,ROOT);Kb=assemble_shared(A,b,3,ROOT)
        assert (Ka-Kb).nnz==0
        assert len(symmetric_dictionary(A,3,ROOT))==968

def test_sociopatterns_source_and_fixed_contact_support():
    archive=ROOT/'experiments/source_data/workplace_InVS_tij.dat.zip'
    records=read_contact_records(archive)
    labels, counts, days, unweighted, weighted=aggregate_network(records)
    assert len(records)==9827 and len(labels)==92 and len(counts)==755
    assert unweighted.shape==(92,92) and np.count_nonzero(unweighted)==1602
    assert (unweighted>0).tolist()==(weighted>0).tolist()
    assert np.allclose(unweighted.sum(axis=1),1)
    assert np.allclose(weighted.sum(axis=1),1)
    assert len(days)>1
    random=matched_graph(92,755,20261112)
    assert np.count_nonzero(random)==1602


def test_additional_generated_regressions():
    import pandas as pd
    d=ROOT/'experiments/data'
    cost=pd.read_csv(d/'carleman_costs.csv')
    assert len(cost)==6*3*5
    emp=pd.read_csv(d/'workplace_topology.csv')
    assert len(emp)==32 and emp.iloc[0]['z3_dim']==124314 and emp.iloc[1]['z3_dim']==124314
    assert emp.iloc[2:]['z2_dim'].eq(3572).all()
    from pathlib import Path
    assert (d/'workplace_residuals.csv').exists()
    report=json.loads((d/'workplace_summary.json').read_text())
    assert report['synthetic_repeats']==30
    assert report['participants']==92 and report['distinct_measured_pairs']==755
    assert np.isclose(report['synthetic_z3_mean'],114605)
    assert np.isclose(report['synthetic_z3_sample_std'],823.7145052789203)
    assert (emp.iloc[2:]['z3_dim']>0).all()
    peaks=pd.read_csv(d/'workplace_residuals.csv')
    assert len(peaks)==32 and peaks['peak_residual_l2'].ge(0).all()
    assert (d/'workplace_daily_contacts.csv').exists()
    acc=pd.read_csv(d/'truncation_accuracy.csv')
    assert len(acc)==8 and acc['max_SEIR_error_l2'].ge(0).all()
    # The order-5 diagnostic is not monotone in maximum finite-horizon error.
    for name in ('Path','Star'):
        case=acc[acc.network==name].set_index('order')
        assert case.loc[5,'max_SEIR_error_l2']>case.loc[4,'max_SEIR_error_l2']
