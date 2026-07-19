from pathlib import Path
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from graph_topologies import (
    normalize_incoming_transmission_intensity,
    path_graph,
    star_graph,
)
from lifting_metrics import cubic_dictionary_metrics, edge_quadratic_dimension


def test_support_and_dictionary_invariance_under_normalization() -> None:
    for graph in (path_graph(10), star_graph(10)):
        normalized = normalize_incoming_transmission_intensity(graph, 1.0)
        assert np.array_equal(graph.adjacency > 0, normalized.adjacency > 0)
        assert np.allclose(normalized.adjacency.sum(axis=1), 1.0)
        assert edge_quadratic_dimension(graph.adjacency) == edge_quadratic_dimension(
            normalized.adjacency
        )
        assert cubic_dictionary_metrics(graph.adjacency) == cubic_dictionary_metrics(
            normalized.adjacency
        )
