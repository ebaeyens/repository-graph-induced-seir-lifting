"""Transmission graphs used in the numerical illustrations.

The adjacency convention follows the article: ``A[i, j] > 0`` means that
infectious individuals at source node ``j`` contribute to the infection
pressure at receiving node ``i``. Diagonal entries represent aggregate
within-subpopulation transmission. The entries encode infection-pressure
couplings, not explicit migration of compartment populations.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class GraphData:
    """One transmission graph and the metadata needed for reproducibility."""

    name: str
    adjacency: np.ndarray
    realization: int | None = None
    seed: int | None = None
    weighting: str = "unit"
    incoming_transmission_intensity: float | None = None

    @property
    def n(self) -> int:
        return int(self.adjacency.shape[0])

    @property
    def m(self) -> int:
        return int(np.count_nonzero(self.adjacency))

    @property
    def diagonal_channels(self) -> int:
        return int(np.count_nonzero(np.diag(self.adjacency)))

    @property
    def off_diagonal_channels(self) -> int:
        return self.m - self.diagonal_channels


def _empty_adjacency(n: int) -> np.ndarray:
    """Allocate a square zero matrix before adding active transmission
    channels.
    """
    if n < 2:
        raise ValueError("The network must contain at least two nodes.")
    return np.zeros((n, n), dtype=float)


def _add_diagonal_channels(adjacency: np.ndarray, weight: float) -> None:
    """Add one aggregate within-population contact per node in place."""
    if weight < 0:
        raise ValueError("Transmission weights must be nonnegative.")
    np.fill_diagonal(adjacency, weight)


def path_graph(
    n: int,
    off_diagonal_weight: float = 1.0,
    diagonal_weight: float = 1.0,
) -> GraphData:
    """Reciprocal directed path plus one diagonal channel at every node."""
    if off_diagonal_weight < 0:
        raise ValueError("Transmission weights must be nonnegative.")

    adjacency = _empty_adjacency(n)
    for node in range(n - 1):
        adjacency[node, node + 1] = off_diagonal_weight
        adjacency[node + 1, node] = off_diagonal_weight
    _add_diagonal_channels(adjacency, diagonal_weight)
    return GraphData("Path", adjacency)


def star_graph(
    n: int,
    off_diagonal_weight: float = 1.0,
    diagonal_weight: float = 1.0,
    hub: int = 0,
) -> GraphData:
    """Reciprocal directed star plus one diagonal channel at every node."""
    if off_diagonal_weight < 0:
        raise ValueError("Transmission weights must be nonnegative.")
    if not 0 <= hub < n:
        raise ValueError("The hub index is outside the network.")

    adjacency = _empty_adjacency(n)
    for node in range(n):
        if node != hub:
            adjacency[hub, node] = off_diagonal_weight
            adjacency[node, hub] = off_diagonal_weight
    _add_diagonal_channels(adjacency, diagonal_weight)
    return GraphData("Star", adjacency)


def sparse_random_graph(
    n: int,
    mean_degree: float,
    off_diagonal_weight: float,
    diagonal_weight: float,
    seed: int,
    realization: int,
) -> GraphData:
    """Directed Erdos--Renyi graph with deterministic diagonal channels.

    Every off-diagonal ordered pair is sampled independently with probability
    ``mean_degree / n``. The diagonal is then filled deterministically.
    """
    if mean_degree <= 0:
        raise ValueError("mean_degree must be positive.")
    if off_diagonal_weight < 0:
        raise ValueError("Transmission weights must be nonnegative.")

    # A fresh PCG64-backed stream makes each adjacency independent of earlier runs.
    rng = np.random.default_rng(seed)
    probability = min(mean_degree / n, 1.0)
    adjacency = (rng.random((n, n)) < probability).astype(float)
    adjacency *= off_diagonal_weight
    np.fill_diagonal(adjacency, 0.0)
    _add_diagonal_channels(adjacency, diagonal_weight)

    return GraphData(
        "Sparse random",
        adjacency,
        realization=realization,
        seed=seed,
    )


def sparse_random_ensemble(
    n: int,
    realizations: int,
    mean_degree: float,
    off_diagonal_weight: float,
    diagonal_weight: float,
    seed: int,
    initial_source_node: int = 0,
    require_initial_source_outgoing_channel: bool = True,
) -> list[GraphData]:
    """Generate the reproducible sparse-random ensemble used in the article.

    When ``require_initial_source_outgoing_channel`` is true, candidate graphs
    are accepted only if the initially infected source node has at least one
    off-diagonal outgoing transmission channel.  Under the convention
    ``A[i, j] > 0``, outgoing channels from source ``j`` are nonzero entries in
    column ``j``.  The criterion is specified before simulation and prevents
    degenerate realizations in which the localized seed cannot reach another
    subpopulation.
    """
    if realizations < 1:
        raise ValueError("At least one random realization is required.")

    if not 0 <= initial_source_node < n:
        raise ValueError("The initial source node is outside the network.")

    seed_generator = np.random.default_rng(seed)
    graphs: list[GraphData] = []
    attempts = 0
    maximum_attempts = max(1000, 100 * realizations)
    while len(graphs) < realizations:
        if attempts >= maximum_attempts:
            raise RuntimeError("Unable to generate the requested admissible ensemble.")
        graph_seed = int(seed_generator.integers(0, 2**32 - 1))
        attempts += 1
        graph = sparse_random_graph(
            n=n,
            mean_degree=mean_degree,
            off_diagonal_weight=off_diagonal_weight,
            diagonal_weight=diagonal_weight,
            seed=graph_seed,
            realization=len(graphs),
        )
        outgoing = np.count_nonzero(graph.adjacency[:, initial_source_node]) - int(
            graph.adjacency[initial_source_node, initial_source_node] > 0.0
        )
        if require_initial_source_outgoing_channel and outgoing < 1:
            continue
        graphs.append(graph)
    return graphs


def normalize_incoming_transmission_intensity(
    graph: GraphData, intensity: float
) -> GraphData:
    """Rescale each row to a common incoming transmission intensity.

    The transformation preserves the exact support and the relative weights
    within each receiving row. Because every graph used here contains a
    positive diagonal channel, every row has positive total weight.
    """
    if not np.isfinite(intensity) or intensity <= 0.0:
        raise ValueError(
            "The incoming transmission intensity must be positive and finite."
        )

    adjacency = np.asarray(graph.adjacency, dtype=float)
    if adjacency.ndim != 2 or adjacency.shape[0] != adjacency.shape[1]:
        raise ValueError("The adjacency matrix must be square.")
    if np.any(~np.isfinite(adjacency)) or np.any(adjacency < 0.0):
        raise ValueError("Transmission weights must be finite and nonnegative.")

    row_sums = adjacency.sum(axis=1)
    if np.any(row_sums <= 0.0):
        raise ValueError("Every receiving row must contain an active channel.")

    normalized = adjacency * (intensity / row_sums)[:, None]

    if not np.array_equal(normalized > 0.0, adjacency > 0.0):
        raise RuntimeError("Incoming-intensity normalization changed the graph support.")
    if not np.allclose(normalized.sum(axis=1), intensity, rtol=0.0, atol=1e-12):
        raise RuntimeError("Incoming-intensity normalization failed its row-sum check.")

    return GraphData(
        name=graph.name,
        adjacency=normalized,
        realization=graph.realization,
        seed=graph.seed,
        weighting="fixed_incoming_transmission_intensity",
        incoming_transmission_intensity=float(intensity),
    )
