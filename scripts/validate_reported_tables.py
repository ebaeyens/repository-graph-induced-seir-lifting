"""Audit numeric manuscript tables against independently regenerated source CSVs.

The journal manuscript is intentionally a separate LaTeX project. For a complete
editorial audit, supply --manuscript /path/to/manuscript, which reads the actual
05_numerics.tex file. In a standalone software deposit, the check instead uses
an explicitly frozen snapshot of those table rows (with provenance), not values
invented from the current CSVs. This avoids a self-validating data pipeline.

The only machine-dependent exception is the *time* column in the matched-cost
table: it is checked against the frozen published measurement run, while the
current regenerated CSV is checked for equal dimensions and CSR storage.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import re
import statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REFERENCE = ROOT / "experiments/reference/manuscript_table_snapshot.json"
COST_REFERENCE = ROOT / "experiments/reference/carleman_costs_reference.csv"


def read_csv(path: Path) -> list[dict]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def select(rows: list[dict], **keys: object) -> dict:
    matches = [r for r in rows if all(str(r[k]) == str(v) for k, v in keys.items())]
    if len(matches) != 1:
        raise AssertionError(f"Expected exactly one row with {keys}; got {len(matches)}")
    return matches[0]


def numbers(cell: str) -> list[tuple[float, float]]:
    """Parse numerical entries and infer their published rounding resolution."""
    text = re.sub(r"\\(?:textbf|boldsymbol)\{([^{}]*)\}", r"\1", cell)
    text = text.replace(r"\pm", "±").replace("$", "")
    found = re.findall(r"[-+]?\d[\d,]*(?:\.\d+)?", text)
    out = []
    for value in found:
        decimals = len(value.rsplit(".", 1)[-1]) if "." in value else 0
        out.append((float(value.replace(",", "")), .51 * 10 ** -decimals + 1e-9))
    return out


def extract_table_rows(tex: str, label: str) -> list[list[str]]:
    anchor = r"\label{" + label + "}"
    if tex.count(anchor) != 1:
        raise AssertionError(f"Manuscript must contain one {label} label")
    section = tex.split(anchor, 1)[1]
    start, end = section.find(r"\midrule"), section.find(r"\bottomrule")
    if start == -1 or end < start:
        raise AssertionError(f"Cannot locate numerical rows for {label}")
    region = section[start + len(r"\midrule"):end]
    rows = []
    for part in region.split(r"\\"):
        part = re.sub(r"\\addlinespace(?:\[[^]]*\])?", "", part)
        if "&" in part:
            cells = [c.strip() for c in part.split("&")]
            rows.append(cells)
    return rows


def read_table_snapshot(manuscript: Path | None) -> tuple[dict, str]:
    if manuscript:
        if manuscript.is_dir():
            manuscript = manuscript / "05_numerics.tex"
        tex = manuscript.read_text(encoding="utf-8")
        table_ids = [
            "tab:network_quantities", "tab:dimension_comparison",
            "tab:residual_summary", "tab:source_sensitivity",
            "tab:cubic_dictionary_size", "tab:carleman_costs",
            "tab:workplace_contacts", "tab:truncation_accuracy",
        ]
        return {k: extract_table_rows(tex, k) for k in table_ids}, str(manuscript)
    raw = json.loads(REFERENCE.read_text(encoding="utf-8"))
    return raw["tables"], str(REFERENCE)


def verify(expected: dict, actual: dict, failures: list[str]) -> int:
    total = 0
    for table_id, rows in expected.items():
        provided = actual.get(table_id, [])
        if len(rows) != len(provided):
            failures.append(f"{table_id}: expected {len(rows)} rows, got {len(provided)}")
            continue
        for i, (item, cells) in enumerate(zip(rows, provided), 1):
            label, values = item
            if len(cells) != len(values) + len(label):
                failures.append(f"{table_id} row {i}: expected {len(label)+len(values)} cells, got {len(cells)}")
                continue
            for k, want in enumerate(label):
                got = " ".join(cells[k].split())
                if got != want:
                    failures.append(f"{table_id} row {i} label {k}: {got!r} != {want!r}")
            for j, ref in enumerate(values, start=len(label)):
                found = numbers(cells[j])
                if len(found) != len(ref):
                    failures.append(f"{table_id} row {i} col {j}: numerical components {len(found)} != {len(ref)}")
                    continue
                for (val, tol), exp in zip(found, ref):
                    total += 1
                    if not math.isfinite(val) or abs(val - exp) > tol:
                        failures.append(f"{table_id} row {i} col {j}: manuscript {val}, CSV {exp:.12g}, round-tol {tol:.5g}")
    return total


def add(target: dict, key: str, rows: list[tuple[list[str], list[list[float]]]]) -> None:
    target[key] = rows


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manuscript", type=Path, help="Actual journal source folder or 05_numerics.tex")
    args = parser.parse_args()
    rows, origin = read_table_snapshot(args.manuscript)
    src = ROOT / "output/data"
    data = ROOT / "experiments/data"
    top = read_csv(src / "network_quantities.csv")
    bench = read_csv(data / "structural_benchmarks.csv")
    cubic = read_csv(src / "cubic_dictionary_size.csv")
    residual = read_csv(src / "residual_sensitivity_summary.csv")
    refined = read_csv(data / "refined_residual_summary.csv")
    sensitivity = read_csv(data / "source_node_sensitivity.csv")
    topo = read_csv(data / "workplace_topology.csv")
    empirical = read_csv(data / "workplace_residuals.csv")
    accuracy = read_csv(data / "truncation_accuracy.csv")
    cost = read_csv(data / "carleman_costs.csv")
    cost_frozen = read_csv(COST_REFERENCE)

    exp: dict = {}
    names = ["Path", "Star", "Sparse random"]
    add(exp, "tab:network_quantities", [([n], [[100], [float(q["m"]), float(q["m_std"])] if n=="Sparse random" else [float(q["m"])], [float(q["Delta_in"]),float(q["Delta_in_std"])] if n=="Sparse random" else [float(q["Delta_in"])], [float(q["delta_max_in"]),float(q["delta_max_in_std"])] if n=="Sparse random" else [float(q["delta_max_in"])]]) for n in names for q in [select(top, network=n, n=100)]])
    add(exp, "tab:dimension_comparison", [([n], [[float(q["ordered_d2"])], [float(q["symmetric_d2"])], [float(q["graph_d2"]),float(q["graph_d2_std"])] if n=="Sparse random" else [float(q["graph_d2"])], [float(q["symmetric_to_graph_d2"])]]) for n in names for q in [select(bench, network=n, n=100)]])
    r_rows = []
    for n in names:
        for wt, label in [("unit", "Unit"), ("fixed_incoming_transmission_intensity", "Normalized")]:
            s = select(residual, network=n, weighting=wt)
            b = select(refined, network=n, weighting=wt)
            random = n=="Sparse random"
            props = [("E2_peak_mean", "E2_peak_sd", "E2_max", "E2_max_std"),
                     ("E2_time_average", "E2_time_average_std", "E2_time_average", "E2_time_average_std"),
                     ("t_peak", "t_peak_std", "t_peak", "t_peak_std"),
                     ("B_refined_mean", "B_refined_sd", "B_refined_mean", "B_refined_sd"),
                     ("ratio_new_mean", "ratio_new_sd", "ratio_new_mean", "ratio_new_sd")]
            vals = [[float((b if idx in (0,3,4) else s)[kp]), float((b if idx in (0,3,4) else s)[ks])] if random else [float((b if idx in (0,3,4) else s)[kp])] for idx,(kp,ks,_,__) in enumerate(props)]
            # The source convention uses different column names in the archived residual summary.
            vals[1] = [float(s["E2_time_average"])] + ([float(s["E2_time_average_std"])] if random else [])
            vals[2] = [float(s["t_peak"])] + ([float(s["t_peak_std"])] if random else [])
            r_rows.append(([("Sparse" if n=="Sparse random" else n) if wt=="unit" else "",label], vals))
    add(exp,"tab:residual_summary",r_rows)
    positions = {( "Path", "end"): "Endpoint", ("Path","middle"):"Middle",("Star","hub"):"Hub",("Star","leaf"):"Leaf"}
    srows=[]
    for n in ["Path","Star"]:
        for wt, lab in [("unit","Unit"),("fixed_incoming_transmission_intensity","Normalized")]:
            for pos in (["end","middle"] if n=="Path" else ["hub","leaf"]):
                q=select(sensitivity,network=n, weighting=wt, initial_position=pos)
                srows.append(([n,lab,positions[n,pos]], [[float(q["E2_max"])],[float(q["t_peak"])] ]))
    add(exp,"tab:source_sensitivity",srows)
    add(exp,"tab:cubic_dictionary_size", [([n], [[float(q["ordered_d3"])], [float(q["symmetric_d3"])], [float(c["Phi2_dim"]),float(c["Phi2_dim_std"])] if n=="Sparse random" else [float(c["Phi2_dim"])], [float(c["Phi3_dim"]),float(c["Phi3_dim_std"])] if n=="Sparse random" else [float(c["Phi3_dim"])], [float(c["z3_edge_dim"]),float(c["z3_edge_dim_std"])] if n=="Sparse random" else [float(c["z3_edge_dim"])]] ) for n in names for q,c in [(select(bench, network=n,n=100),select(cubic,network=n,n=100))]])

    methods=[("Complete symmetric","Symmetric complete"),("Full-Lie reachable","Reachable full Lie"),("Generation/saturation","Split generation/saturation")]
    # Actual method names below checked explicitly to guard accidental renaming.
    method_names=sorted(set(r["method"] for r in cost))
    method_map={
        "Complete symmetric": next((s for s in method_names if "symmetric" in s.lower()), ""),
        "Full-Lie reachable": next((s for s in method_names if "reach" in s.lower()), ""),
        "Generation/saturation": next((s for s in method_names if "split" in s.lower() or "satur" in s.lower()), ""),
    }
    cost_rows=[]
    for n in ["Path","Star"]:
        for presentation, method in method_map.items():
            records=[r for r in cost if r["network"]==n and r["method"]==method and int(r["n"])==12]
            old=[r for r in cost_frozen if r["network"]==n and r["method"]==method and int(r["n"])==12]
            if len(records)!=5 or len(old)!=5:
                raise AssertionError(f"Missing cost runs: {n}/{method}: {len(records)} / {len(old)}")
            for key in ["basis_dim","nnz","csr_bytes"]:
                if len({r[key] for r in records})!=1 or {r[key] for r in records}!={r[key] for r in old}:
                    raise AssertionError(f"Non-reproducible structural cost: {n}/{method}/{key}")
            cost_rows.append(([n,presentation],[[float(records[0]["basis_dim"])],[float(records[0]["csr_bytes"])/1024],[statistics.median(float(r["total_time_s"]) for r in old)]]))
    add(exp,"tab:carleman_costs",cost_rows)

    tq=[r for r in topo if r["type"]=="empirical"]
    eq=[r for r in empirical if r["type"]=="empirical"]
    synth_t=[r for r in topo if r["type"]=="synthetic"]
    synth_e=[r for r in empirical if r["type"]=="synthetic"]
    if len(tq)!=2 or len(eq)!=2 or len(synth_t)!=30 or len(synth_e)!=30:
        raise AssertionError("SocioPatterns expected 2 observed weights and 30 matched graphs")
    e_rows=[]
    for typ,texlab in [("SocioPatterns binary","Measured, binary normalized"),("SocioPatterns duration-weighted","Measured, duration normalized")]:
        r=select(topo,network=typ); v=select(empirical,network=typ)
        e_rows.append(([texlab],[[float(r["max_in_degree_including_diagonal"])],[float(r["z3_dim"])],[float(v["peak_residual_l2"])] ]))
    meanstd=lambda rows,k:[statistics.mean(float(r[k]) for r in rows),statistics.stdev(float(r[k]) for r in rows)]
    e_rows.append(([r"Matched $G(92,755)$ ($N=30$)"], [meanstd(synth_t,"max_in_degree_including_diagonal"),meanstd(synth_t,"z3_dim"),meanstd(synth_e,"peak_residual_l2")]))
    add(exp,"tab:workplace_contacts",e_rows)
    a_rows=[]
    for order in [2,3,4,5]:
        path=select(accuracy,network="Path",order=order)
        star=select(accuracy,network="Star",order=order)
        a_rows.append(([str(order)],[[float(path["dictionary_dim"])],[float(path["max_SEIR_error_l2"])],[float(star["max_SEIR_error_l2"])]]))
    add(exp,"tab:truncation_accuracy",a_rows)

    issues=[]
    count=verify(exp,rows,issues)
    if issues:
        raise SystemExit("TABLE_CROSSCHECK_FAIL\n"+"\n".join(issues))
    print(f"TABLE_CROSSCHECK_PASS: {count} numeric values in 8 manuscript tables verified from CSV; source={origin}")
    print("Cost-table times use frozen measured baseline; current run checks basis dimensions and CSR sizes only.")

if __name__ == "__main__":
    main()
