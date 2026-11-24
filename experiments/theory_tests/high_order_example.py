#!/usr/bin/env python3
"""Illustrative computed constants, not a numerical simulation of the submitted article."""
from fractions import Fraction as F
from pathlib import Path
import math,json
from reachable_closure_check import seir_field,split_hierarchy,lie_monomial
from verify_refinements import monomial_max
n=2
edges=[(0,0,F(1)),(1,1,F(1)),(0,1,F(2,5)),(1,0,F(1,5))]
L,Q=seir_field(n,edges,beta=F(4,5))
H,_=split_hierarchy(n,L,Q,4)
rows=[]
for d in range(2,5):
    P=[]
    for q in sorted(H[d]):
        r=lie_monomial(q,Q,d+1)
        P.append((q,r,sum(abs(v) for v in r.values()),sum(q[2*n:3*n])))
    for p in [F(1),F(1,2),F(1,10)]:
        coeff_sq=sum(C**2 for _,_,C,_ in P)
        power_sq=sum((C*p**(k+1))**2 for _,_,C,k in P)
        simplex_sq=sum((sum(abs(c)*monomial_max(m,p,n) for m,c in rr.items()))**2 for q,rr,C,k in P)
        assert simplex_sq<=power_sq<=coeff_sq
        rows.append(dict(order=d,p=str(p),dimension=len(H[d]),coeff_bound=math.sqrt(float(coeff_sq)),
                         prevalent_bound=math.sqrt(float(power_sq)),simplex_bound=math.sqrt(float(simplex_sq)),
                         simplex_to_prevalence_ratio=math.sqrt(float(simplex_sq/power_sq)) if power_sq>0 else None))
p=Path(__file__).resolve().parents[1]/'results'/'higher_order_example.json'
p.parent.mkdir(parents=True,exist_ok=True)
p.write_text(json.dumps({'note':'Two-node illustrative network, NOT the published n=100 experiment','rows':rows},indent=2))
for r in rows:print(r)
