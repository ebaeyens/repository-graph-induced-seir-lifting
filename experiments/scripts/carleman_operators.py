"""Comparable finite Carleman constructions for the SEIR vector field.

This module intentionally shares a *single* sparse operator assembler across
all dictionary-selection policies. Thus assembly costs do not depend on three
separate implementations with different numerical conventions.

Factor labels are (compartment, zero-based node). Coefficients account for
repeated monomial factors through the product rule. Source j influences
receiving node i when A[i, j] > 0, including diagonal channels.
"""
from __future__ import annotations
from collections import defaultdict, deque
from itertools import combinations_with_replacement
from math import comb
import numpy as np
from scipy.sparse import coo_matrix


def prepare(repo):
    import sys
    p = str(repo / "scripts")
    if p not in sys.path:
        sys.path.insert(0, p)
    from lifting_metrics import canonical_monomial, quadratic_dictionary, linear_saturation, quadratic_successors, incoming_sources
    return canonical_monomial, quadratic_dictionary, linear_saturation, quadratic_successors, incoming_sources


def original_state(n):
    return [((c, i),) for c in "SEIR" for i in range(n)]


def split_dictionary(A, d, repo):
    """Article's generation by f_Q followed by saturation under f_L."""
    canonical, q2, saturation, qsucc, incoming = prepare(repo)
    layers = {1: set(original_state(A.shape[0]))}
    sources = incoming(A)
    if d >= 2:
        layers[2] = q2(A)
    for k in range(3, d + 1):
        seed = set()
        for term in layers[k - 1]:
            seed.update(qsucc(term, sources))
        layers[k] = saturation(seed)
    return sorted(set().union(*(layers.values())))


def reachable_dictionary(A, d, repo):
    """Conventional monomial-support reachability under the full Lie field.

    Unlike split_dictionary, this function does not group same-degree saturation and
    degree raising: it repeatedly differentiates each newly discovered monomial
    by the full vector field, until its truncated support reaches a fixed point.
    It is not a minimal linear invariant subspace construction.
    """
    canonical, _, _, qsucc, incoming = prepare(repo)
    sources = incoming(A)
    seen = set(original_state(A.shape[0]))
    queue = deque(sorted(seen))
    while queue:
        monomial = queue.popleft()
        new = set()
        for c, node in set(monomial):
            if c == "I":
                factors = list(monomial)
                factors.remove((c, node))
                factors.append(("E", node))
                new.add(canonical(factors))
            elif c == "R":
                factors = list(monomial)
                factors.remove((c, node))
                factors.append(("I", node))
                new.add(canonical(factors))
        if len(monomial) < d:
            new.update(qsucc(monomial, sources))
        for successor in sorted(new - seen):
            seen.add(successor)
            queue.append(successor)
    return sorted(seen)


def symmetric_dictionary(A, d, repo):
    """Complete symmetric polynomial basis through degree d (no duplicates)."""
    n = A.shape[0]
    factors = sorted((c, i) for c in "SEIR" for i in range(n))
    return [q for k in range(1, d+1) for q in combinations_with_replacement(factors, k)]


def polynomial_dimension(n, d):
    return sum(comb(4*n+k-1, k) for k in range(1,d+1))


def assemble_shared(A, basis, d, repo, beta=0.8, sigma=0.25, gamma=0.1):
    """Assemble the *same* truncated Lie operator in a supplied monomial basis.

    Each row is the derivative of one observable. Terms of degree d+1 are
    consistently omitted. With a reachable basis, every remaining term must
    be represented; a missing one is an assertion failure, not a silent drop.
    """
    canonical, *_ = prepare(repo)
    pos = {q: i for i,q in enumerate(basis)}
    if len(pos) != len(basis):
        raise ValueError("Duplicate monomial in a benchmark basis")
    coords = []
    values = []
    for row, q in enumerate(basis):
        pol = defaultdict(float)
        for idx, (c, node) in enumerate(q):
            rest = q[:idx] + q[idx+1:]
            if c == "E":
                pol[q] -= sigma
            elif c == "I":
                pol[q] -= gamma
                pol[canonical((*rest,("E",node)))] += sigma
            elif c == "R":
                pol[canonical((*rest,("I",node)))] += gamma
            if c in "SE" and len(q) < d:
                sign = -1.0 if c=="S" else 1.0
                for source in np.flatnonzero(A[node]):
                    dest = canonical((*rest,("S",node),("I",int(source))))
                    pol[dest] += sign*beta*float(A[node,source])
        for new, coef in pol.items():
            if abs(coef) > 1e-13:
                if new not in pos:
                    raise AssertionError(f"Unrepresented degree-{len(new)} term {new}")
                coords.append((row, pos[new]))
                values.append(coef)
    if coords:
        ind = np.array(coords, dtype=np.int64)
        K = coo_matrix((values, (ind[:,0], ind[:,1])), shape=(len(basis), len(basis))).tocsr()
    else:
        K = coo_matrix((len(basis),len(basis))).tocsr()
    K.sum_duplicates(); K.eliminate_zeros()
    return K


def basis_eval(x, basis, n):
    compartment={"S": x[:n],"E": x[n:2*n],"I": x[2*n:3*n],"R": x[3*n:]}
    return np.array([np.prod([compartment[c][i] for c,i in q]) for q in basis],dtype=float)
