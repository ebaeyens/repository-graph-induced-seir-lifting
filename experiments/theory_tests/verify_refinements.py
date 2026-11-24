#!/usr/bin/env python3
"""Exact-rational verification of strengthened SEIR residual estimates.

Independent regression checks; finite tests do not prove the general theorems.
No manuscript, original repository, or review is modified.
"""
from __future__ import annotations
import itertools, random, json, hashlib
from fractions import Fraction as F
from pathlib import Path
from reachable_closure_check import seir_field,split_hierarchy,lie_monomial

BETA=F(4,5)


def F_ki(p, delta_k, a_ki):
    """Exact max_{0<=u<=p}(1-u)[p(delta_k-a_ki)+a_ki u]."""
    assert F(0)<=p<=F(1) and F(0)<=a_ki<=delta_k
    b=delta_k-a_ki
    if a_ki==0:
        u=F(0)
    else:
        u=max(F(0),min(p,(a_ki-b*p)/(2*a_ki)))
    return (1-u)*(b*p+a_ki*u)


def monomial_node_max(alpha, p):
    """Exact maximum of S^s E^e I^i R^r on simplex, with I<=p."""
    s,e,i,r=alpha
    total=s+e+i+r
    if total==0:return F(1)
    v=F(1)
    theta=min(p,F(i,total))
    if i:v*=theta**i
    other=s+e+r
    if other:
        v*=(1-theta)**other
        for exponent in (s,e,r):
            if exponent:v*=F(exponent,other)**exponent
    return v


def monomial_max(mon,p,n):
    v=F(1)
    for k in range(n):
        v*=monomial_node_max((mon[k],mon[n+k],mon[2*n+k],mon[3*n+k]),p)
    return v


def eval_monomial(mon,x):
    v=F(1)
    for exp,xi in zip(mon,x):
        if exp: v*=xi**exp
    return v


def grid(q):
    return [tuple(F(v,q) for v in (s,e,i,q-s-e-i))
            for s in range(q+1) for e in range(q-s+1) for i in range(q-s-e+1)]


def state_vec(local):
    n=len(local)
    return [local[i][c] for c in range(4) for i in range(n)]


def weighted(n,edges):
    A=[[F(0) for _ in range(n)] for _ in range(n)]
    for i,j,w in edges:
        A[i][j]+=w
    delta=[sum(a) for a in A]
    return A,delta


def first_case(n,edges,x):
    A,delta=weighted(n,edges)
    S,E,I,R=x[:n],x[n:2*n],x[2*n:3*n],x[3*n:4*n]
    p=max(I) if I else F(0)
    h=[sum(A[i][j]*I[j] for j in range(n)) for i in range(n)]
    vec_sq=F(0)
    old_graph_sq=F(0)
    new_graph_sq=F(0)
    for i,j,w in edges:
        rsi=-BETA*S[i]*I[j]*h[i]
        rse=BETA*S[i]*(S[j]*h[j]-E[j]*h[i])
        pair_sq=rsi*rsi+rse*rse
        old=BETA*p*max(delta[i],delta[j])
        new=BETA*max(F_ki(p,delta[i],A[i][i]),F_ki(p,delta[j],A[j][i]))
        local=BETA*S[i]*(1-R[j])*max(h[i],h[j])
        assert pair_sq<=local**2
        assert pair_sq<=new**2
        assert new<=old
        vec_sq+=pair_sq
        old_graph_sq+=old**2
        new_graph_sq+=new**2
    assert vec_sq<=new_graph_sq<=old_graph_sq
    return float(vec_sq),float(new_graph_sq),float(old_graph_sq)


def high_case(n,edges,states,max_d):
    L,Q=seir_field(n,edges,beta=BETA)
    dic,_=split_hierarchy(n,L,Q,max_d)
    cnt=0
    strict=0
    maxratio=0.
    for d in range(2,max_d+1):
        polys=[]
        for q in sorted(dic[d]):
            rr=lie_monomial(q,Q,d+1)
            C=sum(abs(c) for c in rr.values())
            iota=sum(q[2*n:3*n])
            assert all(sum(nu[2*n:3*n])==iota+1 for nu in rr)
            polys.append((q,rr,C,iota))
        for local in states:
            x=state_vec(local)
            p=max(x[2*n:3*n]) if n else F(0)
            sum_real=sum_simplex=sum_power=F(0)
            for q,rr,C,iota in polys:
                val=sum(c*eval_monomial(nu,x) for nu,c in rr.items())
                simplex=sum(abs(c)*monomial_max(nu,p,n) for nu,c in rr.items())
                power=C*p**(iota+1)
                assert abs(val)<=simplex<=power
                sum_real+=val**2
                sum_simplex+=simplex**2
                sum_power+=power**2
                cnt+=1
            assert sum_real<=sum_simplex<=sum_power
            if sum_simplex<sum_power:strict+=1
            if sum_power>0: maxratio=max(maxratio,float(sum_simplex/sum_power))
    return cnt,strict,maxratio


def diag_sharp():
    # Exact maxima in the analytically proved one-node case.
    beta=F(1); a=F(1)
    x_inf=[F(2,3),F(0),F(1,3),F(0)]
    x_2=[F(1,2),F(0),F(1,2),F(0)]
    def rr(x):
        S,E,I,R=x
        return -beta*a*S*I*I,beta*a*S*I*(S-E)
    p1=rr(x_inf);p2=rr(x_2)
    assert max(abs(v) for v in p1)==F(4,27)
    assert sum(v*v for v in p2)==F(1,32)
    for st in grid(20):
        rsi,rse=rr(st)
        assert max(abs(rsi),abs(rse))<=F(4,27)
        assert rsi*rsi+rse*rse<=F(1,32)
    return {'exact_infinity_constant':'4/27','exact_euclidean_constant':'1/(4 sqrt(2))',
            'squared_euclidean':'1/32','sharpness_states':{'infinity':'S=2/3,E=0,I=1/3,R=0', 'euclidean':'S=1/2,E=0,I=1/2,R=0'}}


def path_star(n):
    out=[]
    for topology in ['path','star']:
        pairs={(i,i) for i in range(n)}
        for i in range(1,n):
            j=i-1 if topology=='path' else 0
            pairs.add((i,j)); pairs.add((j,i))
        for scheme in ['unit','normalized']:
            counts=[sum(i==r for i,j in pairs) for r in range(n)]
            edges=[(i,j,F(1) if scheme=='unit' else F(1,counts[i])) for i,j in sorted(pairs)]
            A,delta=weighted(n,edges)
            m=len(edges);dmax=max(delta)
            old_sq=(BETA**2)*5*m*dmax*dmax
            previous_sq=(BETA**2)*sum(max(delta[i],delta[j])**2 for i,j,w in edges)
            # p=1 generates a uniform bound independent of epidemic state.
            new_sq=(BETA**2)*sum(max(F_ki(F(1),delta[i],A[i][i]),F_ki(F(1),delta[j],A[j][i]))**2 for i,j,w in edges)
            assert new_sq<=previous_sq<=old_sq
            out.append(dict(topology=topology,scheme=scheme,n=n,m=m,
                            original_bound=float(old_sq)**.5,previous_graph_bound=float(previous_sq)**.5,
                            new_local_simplex_bound=float(new_sq)**.5,
                            improvement_factor_previous_over_new=float(previous_sq/new_sq)**.5))
    return out


def main():
    rr=random.Random(20261111)
    cases=[(1,[]),(1,[(0,0,F(5,3))]),(2,[(0,0,F(1)),(1,1,F(1))]),
           (2,[(0,1,F(2,3)),(1,0,F(3,2))]),
           (3,[(i,j,F(1)) for i in range(3) for j in range(3)]),
           (3,[(0,0,F(1)),(1,0,F(3)),(2,1,F(4,5))])]
    for n in [2,3,4]:
        for z in range(4):
            edges=[(i,j,F(rr.randrange(1,9),rr.randrange(1,9))) for i in range(n) for j in range(n) if rr.random()<.52]
            cases.append((n,edges))
    state_count=0;check_count=0;strict_count=0
    for n,edges in cases:
        loc_grid=grid(2)
        if n<=2:
            states=list(itertools.product(loc_grid,repeat=n))
        else:
            states=[tuple(rr.choice(loc_grid) for i in range(n)) for _ in range(70)]
        for local in states:
            first_case(n,edges,state_vec(local))
        state_count+=len(states)
        high_states=states[:6]
        checks,strict,_=high_case(n,edges,high_states,4 if n<=2 else 3)
        check_count+=checks;strict_count+=strict
    # Rational exact monomial maxima attain given value under an infectious cap.
    for p in [F(0),F(1,4),F(1,2),F(3,4),F(1)]:
        for s in range(4):
            for e in range(3):
                for i in range(3):
                    for r in range(2):
                        m=monomial_node_max((s,e,i,r),p)
                        assert F(0)<=m<=F(1)
                        for st in grid(8):
                            if st[2]<=p:
                                v=st[0]**s*st[1]**e*st[2]**i*st[3]**r
                                assert v<=m
    out={'status':'PASS','rational_arithmetic':True,'new_graph_cases':len(cases),'first_residual_state_checks':state_count,
         'higher_order_component_checks':check_count,'strict_simplex_vs_prevalence_cases':strict_count,
         'topology_100_nodes':path_star(100),'diagonal_only_exact_case':diag_sharp(),
         'theorems_checked':['one-variable sharp bound for S_i h_k','per-edge bound improves existing graph bound',
                             'exact monomial simplex maximum under I<=p','higher-order simplex bound improves coefficient-prevalence bound',
                             'sharp special case with diagonal-only transmission']}
    target=Path(__file__).resolve().parents[1]/'results'/'refinement_checks.json'
    target.parent.mkdir(parents=True,exist_ok=True)
    target.write_text(json.dumps(out,indent=2,ensure_ascii=False),encoding='utf8')
    print(json.dumps(out,indent=2,ensure_ascii=False))
    print('SHA256',hashlib.sha256(target.read_bytes()).hexdigest())

if __name__=='__main__':main()
