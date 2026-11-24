"""Finite-horizon accuracy of successive SEIR graph-induced truncations.

The true trajectory is integrated directly from nonlinear SEIR. Each projected
linear Carleman trajectory is initialized with the same lifted initial state.
Errors are measured in original SEIR coordinates, not in observable space.
The experiment checks finitely many orders and does not claim convergence.
"""
from __future__ import annotations
import argparse,csv,sys
from pathlib import Path
import numpy as np
from scipy.sparse.linalg import expm_multiply
from carleman_operators import split_dictionary,assemble_shared,basis_eval

def run(repo,out,max_order=5,T=12.,points=121):
    sys.path.insert(0,str(repo/'scripts'))
    from graph_topologies import path_graph,star_graph
    from seir_network import SEIRParameters,localized_initial_condition,simulate_seir
    n=3; par=SEIRParameters()
    rows=[]
    for graph in (path_graph(n),star_graph(n)):
        A=graph.adjacency
        initial=localized_initial_condition(n,initial_fraction=.005)
        sol=simulate_seir(A,par,initial,T,points)
        for d in range(2,max_order+1):
            basis=split_dictionary(A,d,repo)
            K=assemble_shared(A,basis,d,repo)
            z0=basis_eval(initial,basis,n)
            # Internal expm_multiply steps may differ from solve_ivp; both have
            # tight tolerances for the small n/finite-time diagnostic.
            predicted=expm_multiply(K,z0,start=0.,stop=T,num=points,endpoint=True)
            idx=[basis.index(((c,i),)) for c in 'SEIR' for i in range(n)]
            original=predicted[:,idx].T
            errors=np.linalg.norm(original-sol.y,axis=0)
            rows.append({'network':graph.name,'n':n,'order':d,'dictionary_dim':len(basis),
                         'horizon':T,'grid_points':points,
                         'max_SEIR_error_l2':float(errors.max()),
                         'final_SEIR_error_l2':float(errors[-1]),
                         'mean_SEIR_error_l2':float(np.trapezoid(errors,sol.t)/T)})
            print('ACCURACY',graph.name,d,len(basis),float(errors.max()),flush=True)
    out.parent.mkdir(parents=True,exist_ok=True)
    with out.open('w',newline='',encoding='utf8') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    return rows
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--repo',required=True,type=Path);p.add_argument('--out',required=True,type=Path)
    a=p.parse_args();run(a.repo,a.out)
