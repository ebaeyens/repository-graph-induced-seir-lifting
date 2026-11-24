"""Fair sparse Carleman operator comparison on identical SEIR supports.

All methods use the same representation, coefficient aggregation, sparse CSR
format, and hardware. The complete symmetric basis includes many redundant
observables but removes Kronecker permutation duplicates. The reachable and
split-generated dictionaries are exactly equal by reachable-closure; differences in measured
running time represent *algorithm implementation costs*, not extra dimension
reduction. Timings vary with the machine and are not theoretical bounds.
"""
from __future__ import annotations
import argparse, csv, json, sys, time, tracemalloc
from pathlib import Path
import numpy as np
from carleman_operators import (split_dictionary, reachable_dictionary, symmetric_dictionary,
                          polynomial_dimension, assemble_shared)

def run(repo, out, repeats=3, sizes=(4, 8, 12)):
    sys.path.insert(0,str(repo/'scripts'))
    from graph_topologies import path_graph, star_graph
    out.parent.mkdir(parents=True,exist_ok=True)
    cases=[path_graph(n) for n in sizes]+[star_graph(n) for n in sizes]
    rows=[]
    method_map={'Symmetric complete':symmetric_dictionary, 'Reachable full Lie':reachable_dictionary,
                'Split generation':split_dictionary}
    for graph in cases:
        A=graph.adjacency; d=3
        bases={name:fn(A,d,repo) for name,fn in method_map.items()}
        assert bases['Split generation']==bases['Reachable full Lie']
        assert len(bases['Symmetric complete'])==polynomial_dimension(graph.n,d)
        # Check actual operator entries, not merely dimension: equal supports
        # must lead to identical coefficients under the common assembler.
        K1=assemble_shared(A,bases['Split generation'],d,repo)
        K2=assemble_shared(A,bases['Reachable full Lie'],d,repo)
        assert (K1 != K2).nnz==0
        for name,fn in method_map.items():
            for rep in range(repeats):
                tracemalloc.start()
                t0=time.perf_counter(); basis=fn(A,d,repo); dict_s=time.perf_counter()-t0
                basis_peak=tracemalloc.get_traced_memory()[1]
                tracemalloc.reset_peak()
                t1=time.perf_counter(); K=assemble_shared(A,basis,d,repo); assemble_s=time.perf_counter()-t1
                py_peak=tracemalloc.get_traced_memory()[1]
                tracemalloc.stop()
                csr=K.data.nbytes+K.indices.nbytes+K.indptr.nbytes
                rows.append({'method':name,'network':graph.name,'n':graph.n,'order':d,'rep':rep+1,
                             'basis_dim':len(basis),'nnz':int(K.nnz),'basis_time_s':dict_s,
                             'assembly_time_s':assemble_s,'total_time_s':dict_s+assemble_s,
                             'Python_peak_bytes':py_peak, 'basis_Python_peak_bytes':basis_peak,
                             'csr_bytes':csr})
        print('PASS',graph.name,graph.n,'reachable',len(bases['Split generation']),
              'symmetric',len(bases['Symmetric complete']),flush=True)
    with out.open('w',newline='',encoding='utf8') as f:
        w=csv.DictWriter(f,fieldnames=rows[0].keys());w.writeheader();w.writerows(rows)
    return rows

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--repo',required=True,type=Path);p.add_argument('--out',required=True,type=Path)
    p.add_argument('--repeats',type=int,default=3);a=p.parse_args()
    run(a.repo,a.out,a.repeats)
