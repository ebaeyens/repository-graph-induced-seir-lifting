#!/usr/bin/env python3
"""Independent, exact-rational comparison of SEIR reachability closures.

Read-only mathematical audit of the CNSNS manuscript, 2026-11-11.
No manuscript, published repository, or submitted data are modified.

Two constructions:
1. Full Lie-support reachability from degree-one state coordinates.
2. Degree-split quadratic transmission generation followed by linear saturation.

Coefficients are exact fractions; repeated factors and all diagonal channels
are explicitly included. Intended as a reproducible small-instance check,
NOT as a substitute for the general mathematical proof.
"""
from __future__ import annotations
from collections import defaultdict
from fractions import Fraction
from itertools import combinations
from hashlib import sha256
from pathlib import Path
import json


def unit(dim, i):
    return tuple(int(j == i) for j in range(dim))


def add_mon(a, b):
    return tuple(x+y for x,y in zip(a,b))


def seir_field(n, edges, beta=Fraction(4,5), sigma=Fraction(1,4), gamma=Fraction(1,10)):
    dim=4*n
    L=[defaultdict(Fraction) for _ in range(dim)]
    Q=[defaultdict(Fraction) for _ in range(dim)]
    for i in range(n):
        L[n+i][unit(dim,n+i)] -= sigma
        L[2*n+i][unit(dim,n+i)] += sigma
        L[2*n+i][unit(dim,2*n+i)] -= gamma
        L[3*n+i][unit(dim,2*n+i)] += gamma
    for i,j,weight in edges:
        assert weight>0
        mon=add_mon(unit(dim,i),unit(dim,2*n+j))
        Q[i][mon] -= beta*weight
        Q[n+i][mon] += beta*weight
    return L,Q


def lie_monomial(monom, field, max_deg):
    # Polynomial terms combined exactly, with like-monomial cancellation.
    out=defaultdict(Fraction)
    for i,power in enumerate(monom):
        if power==0: continue
        downgraded=list(monom)
        downgraded[i] -= 1
        for term,coef in field[i].items():
            new=tuple(a+b for a,b in zip(downgraded, term))
            if sum(new)<=max_deg:
                out[new] += power*coef
    return {x:c for x,c in out.items() if c}


def full_reachable(n, L, Q, d):
    dim=4*n
    F=[]
    for lp,qp in zip(L,Q):
        merged=defaultdict(Fraction)
        for s,c in lp.items(): merged[s]+=c
        for s,c in qp.items(): merged[s]+=c
        F.append(dict(merged))
    seen={unit(dim,i) for i in range(dim)}
    unprocessed=set(seen)
    while unprocessed:
        mon=unprocessed.pop()
        for v in lie_monomial(mon,F,d):
            if v not in seen:
                seen.add(v)
                unprocessed.add(v)
    return {k:{m for m in seen if sum(m)==k} for k in range(1,d+1)}


def saturate(seed,L,d):
    seen=set(seed)
    todo=list(seed)
    while todo:
        p=todo.pop()
        for mon in lie_monomial(p,L,d):
            assert sum(mon)==sum(p)
            if mon not in seen:
                seen.add(mon)
                todo.append(mon)
    return seen


def split_hierarchy(n,L,Q,d):
    dim=4*n
    out={1:{unit(dim,i) for i in range(dim)}}
    seeds={}
    for k in range(2,d+1):
        seed=set()
        for mon in out[k-1]:
            seed.update(lie_monomial(mon,Q,k))
        seed={m for m in seed if sum(m)==k}
        seeds[k]=seed
        out[k]=saturate(seed,L,k)
    return out,seeds


def test_case(case,n,base_edges,d=3):
    edges=[(i,j, Fraction((i+1)*(j+2), 1)) for i,j in base_edges]
    L,Q=seir_field(n,edges)
    full=full_reachable(n,L,Q,d)
    split,seeds=split_hierarchy(n,L,Q,d)
    equal={k:full[k]==split[k] for k in range(1,d+1)}
    assert all(equal.values()), f'Mismatch in {case}: '+str(equal)
    return {'case':case,'n':n,'channels':len(edges),'max_degree':d,
            'generation_seed_counts':{str(k):len(v) for k,v in seeds.items()},
            'full_reachable_counts':{str(k):len(v) for k,v in full.items()},
            'split_saturated_counts':{str(k):len(v) for k,v in split.items()},
            'cumulative_counts':{str(k):sum(len(split[j]) for j in range(1,k+1)) for k in range(1,d+1)},
            'degreewise_exact_set_equality':{str(k):equal[k] for k in equal}}


def main():
    cases={
      'corridor_3_nodes':(3,[(0,0),(0,1),(1,0),(1,1),(1,2),(2,1),(2,2)],4),
      'single_node_diagonal':(1,[(0,0)],5),
      '2_nodes_directed_with_loops':(2,[(0,0),(1,1),(0,1)],4),
      '2_nodes_reciprocal_with_loops':(2,[(0,0),(1,1),(0,1),(1,0)],4),
      '3_nodes_no_diagonals':(3,[(0,1),(1,0),(1,2),(2,1)],3),
      '3_nodes_complete_with_diagonals':(3,list(__import__('itertools').product(range(3),repeat=2)),3),
    }
    results=[]
    for name,(n,edges,d) in cases.items():
        print('running',name,flush=True)
        results.append(test_case(name,n,edges,d))
    target=results[0]
    assert target['split_saturated_counts']['2']==14
    assert target['split_saturated_counts']['3']==67
    assert target['generation_seed_counts']['3']==42
    assert target['cumulative_counts']['2']==26
    assert target['cumulative_counts']['3']==93
    report={'purpose':'Audit equality of split SEIR dictionary with full Lie-reachable monomials',
            'version':'2026-11-11', 'exact_fraction_arithmetic':True,
            'statement':'Observed exact set equality in all tested cases and degrees; finite tests are not a general proof.',
            'cases':results}
    out=Path(__file__).with_suffix('.json')
    out.write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps(report,indent=2))
    print('sha256 script',sha256(Path(__file__).read_bytes()).hexdigest())
    print('sha256 results',sha256(out.read_bytes()).hexdigest())

if __name__=='__main__':
    main()
