"""Measured workplace contacts: reproducible structural SEIR benchmark.

The input is the original SocioPatterns InVS temporal contact archive. A row
``t person_1 person_2`` represents proximity in the preceding 20-second
window, not a transmission event. The entire observation period is aggregated
into a fixed undirected support: one edge for each distinct observed pair.

For compatibility with the article's *population-level* network SEIR equations,
each contact participant is used as an index for a model node, and an assumed
within-node channel is added. The diagonal is a modelling convention, not a
measured within-person contact. Accordingly, this is a structural experiment,
not an individual-level calibrated disease forecast. Contact duration supplies
only an illustrative *relative* weight; every receiving row is normalized,
including its diagonal channel, to sum to one. All synthetic comparators have
the same number of nodes and undirected edges, with independently fixed seeds.

Running this script needs no network access and does not access private files.
"""
from __future__ import annotations

import argparse
from collections import Counter
import csv
import hashlib
import json
from pathlib import Path
import sys
import zipfile

import numpy as np

# SHA-256 of the author's exact copy of SocioPatterns' public archive.
DATA_SHA256 = "bf818f7e819864e134c90ed82f2cda6ca9d9548d43fe4d05002ac068c91258c0"
SEED_START = 20261112
REPEATS = 30


def read_contact_records(archive: Path):
    """Load and validate the raw [time, anonymized i, anonymized j] records."""
    actual = hashlib.sha256(archive.read_bytes()).hexdigest()
    if actual != DATA_SHA256:
        raise ValueError(f"Unexpected source archive SHA-256: {actual}")
    with zipfile.ZipFile(archive) as compressed:
        if compressed.namelist() != ["tij_InVS.dat"]:
            raise ValueError("Unexpected files inside SocioPatterns archive")
        with compressed.open("tij_InVS.dat") as source:
            records = np.loadtxt(source, dtype=np.int64)
    if records.ndim != 2 or records.shape[1] != 3:
        raise ValueError("Expected three columns: t i j")
    if np.any(records[:, 1] == records[:, 2]) or np.any(records[:, 0] % 20):
        raise ValueError("Invalid source/target ID or non-20-second timestamp")
    if len({(int(t), *sorted((int(i), int(j)))) for t, i, j in records}) != len(records):
        raise ValueError("Duplicate undirected contact per time interval")
    return records


def aggregate_network(records):
    """Return anonymous indexing, observed pair counts and two fixed SEIR matrices.

    The unweighted network and duration-weighted network have exactly the same
    support. A positive diagonal term with weight 1 is assumed in both cases;
    the duration weight on an off-diagonal edge is count / max_pair_count.
    Normalization acts on receiving rows and leaves the support unchanged.
    """
    labels = sorted(set(records[:, 1]) | set(records[:, 2]))
    indexing = {int(label): k for k, label in enumerate(labels)}
    counts: Counter[tuple[int, int]] = Counter()
    by_day: dict[int, Counter[tuple[int, int]]] = {}
    for t, first, second in records:
        edge = tuple(sorted((indexing[int(first)], indexing[int(second)])))
        counts[edge] += 1
        by_day.setdefault(int(t)//86400, Counter())[edge] += 1
    n = len(labels)
    binary = np.eye(n, dtype=float)
    weighted = np.eye(n, dtype=float)
    max_count = max(counts.values())
    for (i, j), count in counts.items():
        binary[i, j] = binary[j, i] = 1.0
        weighted[i, j] = weighted[j, i] = count / max_count
    binary /= binary.sum(axis=1, keepdims=True)
    weighted /= weighted.sum(axis=1, keepdims=True)
    return labels, counts, by_day, binary, weighted


def matched_graph(n: int, n_edges: int, seed: int):
    """Uniform G(n,m) support with an assumed diagonal and row sum one."""
    pairs = [(i, j) for i in range(n) for j in range(i+1, n)]
    rng = np.random.default_rng(seed)
    picks = rng.choice(len(pairs), size=n_edges, replace=False)
    adjacency = np.eye(n, dtype=float)
    for pick in picks:
        i, j = pairs[int(pick)]
        adjacency[i, j] = adjacency[j, i] = 1.0
    return adjacency / adjacency.sum(axis=1, keepdims=True)


def csv_write(destination: Path, rows):
    if not rows:
        return
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("w", newline="", encoding="utf8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def run(repo: Path, output_dir: Path, repeats: int = REPEATS):
    """Generate structural, time-aggregation and residual summaries.

    The SEIR time coordinate is nondimensional and does not follow the 2013
    calendar. The initial model node is the smallest anonymous source label.
    No within-person transmission or epidemiological rates are inferred from
    the measured interaction file.
    """
    archive = repo / "experiments/source_data/workplace_InVS_tij.dat.zip"
    records = read_contact_records(archive)
    labels, counts, daily, binary, weighted = aggregate_network(records)
    n, links = len(labels), len(counts)
    if (len(records), n, links) != (9827, 92, 755):
        raise AssertionError("Unexpected number of observed records/nodes/pairs")
    sys.path.insert(0, str(repo / "scripts"))
    from lifting_metrics import cubic_dictionary_metrics
    from seir_network import SEIRParameters, localized_initial_condition, simulate_seir
    from residuals import residual_time_series

    # Structure is unchanged by nonzero weight rescaling. Still compute the
    # dictionary independently for each weighting, as a guard against regressions.
    examples = [
        ("SocioPatterns binary", "empirical", -1, binary),
        ("SocioPatterns duration-weighted", "empirical", -1, weighted),
    ]
    examples.extend((f"Matched G(n,m) {SEED_START+rep}", "synthetic", SEED_START+rep,
                     matched_graph(n, links, SEED_START+rep)) for rep in range(repeats))
    structures, residuals = [], []
    parameters = SEIRParameters()
    x0 = localized_initial_condition(n, initial_fraction=1e-3)
    for name, kind, seed, matrix in examples:
        dimension = cubic_dictionary_metrics(matrix)
        counts_per_node = np.count_nonzero(matrix, axis=1)
        structures.append({
            "network": name, "type": kind, "seed": seed, "n": n,
            "observed_pairs_or_matched_edges": links,
            "directed_channels_including_diagonal": int(np.count_nonzero(matrix)),
            "max_in_degree_including_diagonal": int(counts_per_node.max()),
            "z2_dim": 4*n + int(dimension["Phi2_dim"]),
            "Phi3_dim": int(dimension["Phi3_dim"]),
            "z3_dim": int(dimension["z3_edge_dim"]),
            "incoming_intensity_min": float(matrix.sum(axis=1).min()),
            "incoming_intensity_max": float(matrix.sum(axis=1).max()),
        })
        solution = simulate_seir(matrix, parameters, x0, 60.0, 401)
        curve = residual_time_series(solution.y, matrix, parameters)
        residuals.append({
            "network": name, "type": kind, "seed": seed,
            "model_horizon": 60, "time_grid_points": 401,
            "initial_anonymous_participant_id": int(labels[0]),
            "peak_residual_l2": float(curve.max()),
            "peak_residual_time": float(solution.t[int(np.argmax(curve))]),
            "peak_RMS_per_coordinate": float(curve.max()/np.sqrt(2*np.count_nonzero(matrix))),
        })
    daily_rows = []
    for day, pairs in sorted(daily.items()):
        participants = {idx for pair in pairs for idx in pair}
        daily_rows.append({"day_index": day,
                           "number_of_20_second_pair_records": sum(pairs.values()),
                           "number_of_distinct_pairs": len(pairs),
                           "number_of_active_participants": len(participants)})
    output_dir.mkdir(parents=True, exist_ok=True)
    csv_write(output_dir/"workplace_topology.csv", structures)
    csv_write(output_dir/"workplace_residuals.csv", residuals)
    csv_write(output_dir/"workplace_daily_contacts.csv", daily_rows)
    synthetic = np.array([row["z3_dim"] for row in structures if row["type"]=="synthetic"])
    synthetic_peak = np.array([row["peak_residual_l2"] for row in residuals if row["type"]=="synthetic"])
    summary = {
        "dataset": "SocioPatterns workplace InVS, France, 24 June to 3 July 2013",
        "license": "CC0 Public Domain Dedication",
        "archive_sha256": DATA_SHA256, "records": len(records),
        "contact_windows_seconds": 20, "unique_timestamps": len(np.unique(records[:,0])),
        "participants": n, "distinct_measured_pairs": links,
        "total_recorded_pair_seconds": len(records)*20,
        "number_of_directed_model_channels_including_assumed_diagonal": n+2*links,
        "network_source": "https://sociopatterns.org/datasets/contacts-in-a-workplace/",
        "citation_doi": "10.1017/nws.2015.10",
        "aggregation": "Undirected union of contacts over full observation period",
        "duration_weight_rule": "off-diagonal count / max pair count; diagonal 1; normalize every receiving row",
        "synthetic_repeats": repeats, "synthetic_seeds": list(range(SEED_START,SEED_START+repeats)),
        "synthetic_z3_mean": float(synthetic.mean()),
        "synthetic_z3_sample_std": float(synthetic.std(ddof=1)),
        "synthetic_peak_mean": float(synthetic_peak.mean()),
        "synthetic_peak_sample_std": float(synthetic_peak.std(ddof=1)),
        "epidemiological_calibration": False,
        "temporal_network_used_for_SEIR_dynamics": False,
        "diagonal_channels_measured": False,
    }
    (output_dir/"workplace_summary.json").write_text(json.dumps(summary, indent=2)+"\n", encoding="utf8")
    print("SOCIOPATTERNS_PASS", {key:summary[key] for key in
          ("records","participants","distinct_measured_pairs","synthetic_z3_mean")}, flush=True)
    return structures, residuals, summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--repeats", type=int, default=REPEATS)
    args = parser.parse_args()
    run(args.repo.resolve(), args.out.resolve(), args.repeats)
