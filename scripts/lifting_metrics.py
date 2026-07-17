"""Dimensions of complete and graph-induced tensor liftings.

A monomial is stored as a sorted tuple of ``(compartment, node)`` factors.
Sorting makes multiplication commutative, while repeated factors remain
explicit. The dictionary recursion follows Algorithm 1 of the article:
quadratic generation of the next degree followed by linear closure within that
degree.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import TypeAlias

import numpy as np


Factor: TypeAlias = tuple[str, int]
Monomial: TypeAlias = tuple[Factor, ...]


def complete_quadratic_dimension(n: int) -> int:
    return 4 * n + (4 * n) ** 2


def complete_cubic_dimension(n: int) -> int:
    return 4 * n + (4 * n) ** 2 + (4 * n) ** 3


def edge_quadratic_dimension(adjacency: np.ndarray) -> int:
    n = adjacency.shape[0]
    m = int(np.count_nonzero(adjacency))
    return 4 * n + 2 * m


def network_metrics(adjacency: np.ndarray) -> dict[str, float]:
    """Return the graph quantities displayed in Section 5."""
    n = adjacency.shape[0]
    m = int(np.count_nonzero(adjacency))
    diagonal = int(np.count_nonzero(np.diag(adjacency)))
    return {
        "n": n,
        "m": m,
        "m_diagonal": diagonal,
        "m_off_diagonal": m - diagonal,
        "Delta_in": int(np.max(np.count_nonzero(adjacency, axis=1))),
        "delta_max_in": float(np.max(adjacency.sum(axis=1))),
    }


def canonical_monomial(factors: Iterable[Factor]) -> Monomial:
    return tuple(sorted(factors))


def active_channels(adjacency: np.ndarray) -> list[tuple[int, int]]:
    receiving, source = np.nonzero(adjacency)
    return [
        (int(i), int(j))
        for i, j in zip(receiving, source, strict=True)
    ]


def incoming_sources(adjacency: np.ndarray) -> dict[int, tuple[int, ...]]:
    return {
        node: tuple(int(source) for source in np.flatnonzero(adjacency[node]))
        for node in range(adjacency.shape[0])
    }


def quadratic_dictionary(adjacency: np.ndarray) -> set[Monomial]:
    """Return the closed degree-two dictionary ``{S_i I_j, S_i E_j}``."""
    dictionary: set[Monomial] = set()
    for receiving, source in active_channels(adjacency):
        dictionary.add(canonical_monomial((("S", receiving), ("I", source))))
        dictionary.add(canonical_monomial((("S", receiving), ("E", source))))
    return dictionary


def _replace_one(
    monomial: Monomial,
    old_factor: Factor,
    new_factor: Factor,
) -> Monomial:
    factors = list(monomial)
    factors.remove(old_factor)
    factors.append(new_factor)
    return canonical_monomial(factors)


def linear_successors(monomial: Monomial) -> set[Monomial]:
    """Same-degree monomials created by ``I_i -> E_i`` transitions."""
    successors: set[Monomial] = set()
    for compartment, node in set(monomial):
        if compartment == "I":
            successors.add(
                _replace_one(monomial, ("I", node), ("E", node))
            )
    return successors


def linear_closure(seeds: Iterable[Monomial]) -> set[Monomial]:
    """Iterate the linear closure until no new monomial appears."""
    closed = set(seeds)
    frontier = list(closed)
    while frontier:
        monomial = frontier.pop()
        for successor in linear_successors(monomial):
            if successor not in closed:
                closed.add(successor)
                frontier.append(successor)
    return closed


def quadratic_successors(
    monomial: Monomial,
    sources: Mapping[int, tuple[int, ...]],
) -> set[Monomial]:
    """Next-degree monomials created by the quadratic transmission field."""
    successors: set[Monomial] = set()

    # Multiplicities change coefficients but not membership of the dictionary,
    # so one structural successor per distinct factor is sufficient here.
    for compartment, node in set(monomial):
        if compartment == "S":
            for source in sources[node]:
                successors.add(
                    canonical_monomial((*monomial, ("I", source)))
                )
        elif compartment == "E":
            for source in sources[node]:
                factors = list(monomial)
                factors.remove(("E", node))
                factors.extend((("S", node), ("I", source)))
                successors.add(canonical_monomial(factors))
    return successors


def cubic_dictionary_metrics(adjacency: np.ndarray) -> dict[str, int]:
    """Return the degree-two and linearly closed degree-three sizes."""
    phi2 = quadratic_dictionary(adjacency)
    sources = incoming_sources(adjacency)

    cubic_seeds: set[Monomial] = set()
    for monomial in phi2:
        cubic_seeds.update(quadratic_successors(monomial, sources))

    phi3 = linear_closure(cubic_seeds)
    n = adjacency.shape[0]
    return {
        "Phi2_dim": len(phi2),
        "Phi3_seed_dim": len(cubic_seeds),
        "Phi3_linear_closure_additions": len(phi3 - cubic_seeds),
        "Phi3_dim": len(phi3),
        "z3_edge_dim": 4 * n + len(phi2) + len(phi3),
    }
