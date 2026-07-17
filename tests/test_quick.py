from pathlib import Path
import sys
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from graph_topologies import path_graph, star_graph, normalize_incoming_transmission_intensity
from lifting_metrics import edge_quadratic_dimension, cubic_dictionary_metrics

for graph in (path_graph(10), star_graph(10)):
    normalized = normalize_incoming_transmission_intensity(graph, 1.0)
    assert np.array_equal(graph.adjacency > 0, normalized.adjacency > 0)
    assert np.allclose(normalized.adjacency.sum(axis=1), 1.0)
    assert edge_quadratic_dimension(graph.adjacency) == edge_quadratic_dimension(normalized.adjacency)
    assert cubic_dictionary_metrics(graph.adjacency) == cubic_dictionary_metrics(normalized.adjacency)

counts = ROOT / "examples" / "three_city_algorithm1_example" / "data" / "three_city_dictionary_counts.csv"
assert counts.exists()
print("Quick validation passed.")
