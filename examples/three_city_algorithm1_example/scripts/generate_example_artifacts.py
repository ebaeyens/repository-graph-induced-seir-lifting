#!/usr/bin/env python3
"""Generate and verify all machine-readable artifacts for the three-city example.

The script implements Algorithm 1 used in the manuscript:

1. Decompose the vector field into linear and quadratic parts.
2. Build degree-two transmission seeds.
3. Close each homogeneous dictionary under the linear SEIR dynamics.
4. Use the quadratic transmission field to generate the next degree.
5. Canonicalize commutative monomials and merge duplicates.
6. Verify linear closure and report the next-degree truncation forcing.

Only the Python standard library is required.
"""

from __future__ import annotations

import csv
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
GENERATED_DIR = ROOT / "generated"

N = 3
EDGES: tuple[tuple[int, int], ...] = (
    (1, 1),
    (1, 2),
    (2, 1),
    (2, 2),
    (2, 3),
    (3, 2),
    (3, 3),
)

VARIABLES: tuple[tuple[str, int], ...] = tuple(
    [("S", i) for i in range(1, N + 1)]
    + [("E", i) for i in range(1, N + 1)]
    + [("I", i) for i in range(1, N + 1)]
)
INDEX = {variable: position for position, variable in enumerate(VARIABLES)}

NEIGHBORS: dict[int, tuple[int, ...]] = {
    i: tuple(j for receiver, j in EDGES if receiver == i)
    for i in range(1, N + 1)
}

Monomial = tuple[int, ...]


@dataclass(frozen=True)
class GenerationRecord:
    source: Monomial
    generated: Monomial
    sign: int
    edge: tuple[int, int]
    mechanism: str


def monomial(factors: Iterable[tuple[str, int]]) -> Monomial:
    exponents = [0] * len(VARIABLES)
    for factor in factors:
        exponents[INDEX[factor]] += 1
    return tuple(exponents)


def add_factor(q: Monomial, factor: tuple[str, int], multiplicity: int = 1) -> Monomial:
    exponents = list(q)
    exponents[INDEX[factor]] += multiplicity
    return tuple(exponents)


def remove_factor(q: Monomial, factor: tuple[str, int], multiplicity: int = 1) -> Monomial:
    exponents = list(q)
    position = INDEX[factor]
    if exponents[position] < multiplicity:
        raise ValueError(f"Cannot remove {multiplicity} copies of {factor} from {q}")
    exponents[position] -= multiplicity
    return tuple(exponents)


def replace_factor(q: Monomial, old: tuple[str, int], new: tuple[str, int]) -> Monomial:
    return add_factor(remove_factor(q, old), new)


def degree(q: Monomial) -> int:
    return sum(q)


def factors(q: Monomial) -> list[tuple[str, int]]:
    result: list[tuple[str, int]] = []
    for variable, exponent in zip(VARIABLES, q, strict=True):
        result.extend([variable] * exponent)
    return result


def factor_counts(q: Monomial) -> dict[str, int]:
    counts = {"S": 0, "E": 0, "I": 0}
    for (kind, _), exponent in zip(VARIABLES, q, strict=True):
        counts[kind] += exponent
    return counts


def family(q: Monomial) -> str:
    """Return the customary family label used in the manuscript."""
    counts = factor_counts(q)
    key = (counts["S"], counts["E"], counts["I"])
    labels = {
        (1, 0, 2): "SII",
        (1, 1, 1): "SIE",
        (1, 2, 0): "SEE",
        (2, 0, 1): "SSI",
        (2, 1, 0): "SSE",
        (1, 0, 1): "SI",
        (1, 1, 0): "SE",
    }
    return labels.get(key, f"S{counts['S']}E{counts['E']}I{counts['I']}")


def factor_signature(q: Monomial) -> tuple[tuple[int, int], ...]:
    kind_order = {"S": 0, "E": 1, "I": 2}
    return tuple((kind_order[kind], node) for kind, node in factors(q))


def natural_key(q: Monomial) -> tuple:
    """Stable ordering by scientific family and then factor indices."""
    family_order = {"SII": 0, "SIE": 1, "SEE": 2, "SSI": 3, "SSE": 4}
    return (family_order.get(family(q), 99), factor_signature(q))


def m2_key(q: Monomial) -> tuple:
    fam = family(q)
    fam_order = {"SI": 0, "SE": 1}
    # Each degree-two coordinate has one susceptible factor and one I/E factor.
    s_node = next(node for (kind, node), exponent in zip(VARIABLES, q, strict=True) if kind == "S" and exponent)
    other_kind = "I" if fam == "SI" else "E"
    other_node = next(node for (kind, node), exponent in zip(VARIABLES, q, strict=True) if kind == other_kind and exponent)
    return (fam_order[fam], s_node, other_node)


def format_factor_tex(kind: str, node: int, exponent: int) -> str:
    base = rf"{kind}_{node}"
    return base if exponent == 1 else rf"{base}^{{{exponent}}}"


def format_monomial_tex(q: Monomial) -> str:
    parts: list[str] = []
    for (kind, node), exponent in zip(VARIABLES, q, strict=True):
        if exponent:
            parts.append(format_factor_tex(kind, node, exponent))
    return "".join(parts) if parts else "1"


def format_monomial_plain(q: Monomial) -> str:
    parts: list[str] = []
    for (kind, node), exponent in zip(VARIABLES, q, strict=True):
        if exponent == 1:
            parts.append(f"{kind}{node}")
        elif exponent > 1:
            parts.append(f"{kind}{node}^{exponent}")
    return "*".join(parts) if parts else "1"


def linear_generated_terms(q: Monomial) -> set[Monomial]:
    """Return same-degree monomials in L_{f_L} q, ignoring coefficients.

    The original monomial is included whenever the derivative has a nonzero
    diagonal linear contribution. Each infectious factor may also be replaced
    by the exposed factor with the same node index.
    """
    generated: set[Monomial] = set()
    if any(q[INDEX[(kind, i)]] for kind in ("E", "I") for i in range(1, N + 1)):
        generated.add(q)
    for i in range(1, N + 1):
        if q[INDEX[("I", i)]]:
            generated.add(replace_factor(q, ("I", i), ("E", i)))
    return generated


def linear_closure(seeds: Iterable[Monomial]) -> set[Monomial]:
    closure = set(seeds)
    while True:
        expanded = set(closure)
        for q in closure:
            expanded.update(linear_generated_terms(q))
        if expanded == closure:
            return closure
        closure = expanded


def quadratic_generation_records(q: Monomial) -> list[GenerationRecord]:
    """Return coefficient-aware monomial appearances in L_{f_Q} q.

    The scalar coefficient is represented by sign, multiplicity, and edge.
    Only dictionary membership is needed for most tables; multiplicities are
    retained to detect within-row algebraic duplicates correctly.
    """
    records: list[GenerationRecord] = []
    for i in range(1, N + 1):
        s_count = q[INDEX[("S", i)]]
        e_count = q[INDEX[("E", i)]]
        for j in NEIGHBORS[i]:
            if s_count:
                generated = add_factor(q, ("I", j))
                records.append(
                    GenerationRecord(
                        source=q,
                        generated=generated,
                        sign=-s_count,
                        edge=(i, j),
                        mechanism=f"differentiate S{i}",
                    )
                )
            if e_count:
                generated = remove_factor(q, ("E", i))
                generated = add_factor(generated, ("S", i))
                generated = add_factor(generated, ("I", j))
                records.append(
                    GenerationRecord(
                        source=q,
                        generated=generated,
                        sign=e_count,
                        edge=(i, j),
                        mechanism=f"differentiate E{i}",
                    )
                )
    return records


def combine_within_derivative(records: Iterable[GenerationRecord]) -> dict[Monomial, list[GenerationRecord]]:
    """Combine algebraically identical terms within one scalar derivative.

    Coefficients associated with different edge weights remain distinct. Terms
    associated with the same edge are summed, and exact zero coefficients are
    removed before dictionary membership is determined.
    """
    grouped: dict[Monomial, dict[tuple[int, int], list[GenerationRecord]]] = defaultdict(lambda: defaultdict(list))
    for record in records:
        grouped[record.generated][record.edge].append(record)

    combined: dict[Monomial, list[GenerationRecord]] = {}
    for generated, by_edge in grouped.items():
        retained: list[GenerationRecord] = []
        for edge, edge_records in by_edge.items():
            coefficient = sum(record.sign for record in edge_records)
            if coefficient == 0:
                continue
            mechanisms = "; ".join(sorted({record.mechanism for record in edge_records}))
            retained.append(
                GenerationRecord(
                    source=edge_records[0].source,
                    generated=generated,
                    sign=coefficient,
                    edge=edge,
                    mechanism=mechanisms,
                )
            )
        if retained:
            combined[generated] = retained
    return combined


def generate_next_degree(dictionary: Iterable[Monomial]) -> tuple[set[Monomial], dict[Monomial, dict[Monomial, list[GenerationRecord]]]]:
    sources: dict[Monomial, dict[Monomial, list[GenerationRecord]]] = {}
    seeds: set[Monomial] = set()
    for q in dictionary:
        combined = combine_within_derivative(quadratic_generation_records(q))
        sources[q] = combined
        seeds.update(combined)
    return seeds, sources


def seed_origin(q: Monomial, seeds: set[Monomial]) -> str:
    return "quadratic seed" if q in seeds else "linear closure"


def write_csvs(
    m2_seeds: set[Monomial],
    m2: set[Monomial],
    m3_seeds: set[Monomial],
    m3: set[Monomial],
    m3_sources: dict[Monomial, dict[Monomial, list[GenerationRecord]]],
    m4_seeds: set[Monomial],
    m4: set[Monomial],
) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    counts = [
        ("channels", len(EDGES)),
        ("M2_seed_count", len(m2_seeds)),
        ("M2_count", len(m2)),
        ("raw_cubic_appearances", sum(len(records) for records in m3_sources.values())),
        ("M3_seed_count", len(m3_seeds)),
        ("M3_linear_closure_additions", len(m3 - m3_seeds)),
        ("M3_count", len(m3)),
        ("dim_x", 12),
        ("dim_z2", 12 + len(m2)),
        ("dim_z3", 12 + len(m2) + len(m3)),
        ("M4_seed_count", len(m4_seeds)),
        ("M4_count", len(m4)),
    ]
    with (DATA_DIR / "three_city_dictionary_counts.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["quantity", "value"])
        writer.writerows(counts)

    ordered_m3 = sorted(m3, key=natural_key)
    with (DATA_DIR / "three_city_m3_dictionary.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["index", "family", "monomial", "origin"])
        for index_value, q in enumerate(ordered_m3, start=1):
            writer.writerow([index_value, family(q), format_monomial_plain(q), seed_origin(q, m3_seeds)])

    generating_rows: dict[Monomial, list[Monomial]] = defaultdict(list)
    for source, generated_map in m3_sources.items():
        for generated in generated_map:
            generating_rows[generated].append(source)
    shared = [(q, sources) for q, sources in generating_rows.items() if len(sources) > 1]
    shared.sort(key=lambda item: natural_key(item[0]))
    with (DATA_DIR / "shared_cubic_coordinates.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["monomial", "source_1", "source_2"])
        for q, sources in shared:
            writer.writerow(
                [
                    format_monomial_plain(q),
                    format_monomial_plain(sources[0]),
                    format_monomial_plain(sources[1]),
                ]
            )


def tex_escape(text: str) -> str:
    return text.replace("_", r"\_")


def write_generated_tex(
    m2: set[Monomial],
    m3_seeds: set[Monomial],
    m3: set[Monomial],
    m3_sources: dict[Monomial, dict[Monomial, list[GenerationRecord]]],
    m4_seeds: set[Monomial],
    m4: set[Monomial],
) -> None:
    GENERATED_DIR.mkdir(parents=True, exist_ok=True)

    raw = sum(len(records) for records in m3_sources.values())
    counts_tex = rf"""% Generated by scripts/generate_example_artifacts.py
\newcommand{{\NumChannels}}{{{len(EDGES)}}}
\newcommand{{\NumMtwo}}{{{len(m2)}}}
\newcommand{{\NumRawCubic}}{{{raw}}}
\newcommand{{\NumMthreeSeeds}}{{{len(m3_seeds)}}}
\newcommand{{\NumMthreeClosure}}{{{len(m3 - m3_seeds)}}}
\newcommand{{\NumMthree}}{{{len(m3)}}}
\newcommand{{\DimZtwo}}{{{12 + len(m2)}}}
\newcommand{{\DimZthree}}{{{12 + len(m2) + len(m3)}}}
\newcommand{{\NumMfourSeeds}}{{{len(m4_seeds)}}}
\newcommand{{\NumMfour}}{{{len(m4)}}}
"""
    (GENERATED_DIR / "counts.tex").write_text(counts_tex, encoding="utf-8")

    ordered_m2 = sorted(m2, key=m2_key)
    table_lines: list[str] = []
    for q in ordered_m2:
        generated = sorted(m3_sources[q], key=natural_key)
        rhs = r",\ ".join(rf"${format_monomial_tex(term)}$" for term in generated)
        table_lines.append(rf"${format_monomial_tex(q)}$ & {rhs} \\")
    row_text = "% Generated by scripts/generate_example_artifacts.py\n" + "\n".join(table_lines) + "\n"
    (GENERATED_DIR / "cubic_generation_rows.tex").write_text(row_text, encoding="utf-8")
    cubic_table = r"""% Generated by scripts/generate_example_artifacts.py
\begin{longtable}{@{}>{\raggedright\arraybackslash}p{0.17\textwidth}>{\raggedright\arraybackslash}p{0.76\textwidth}@{}}
\caption{Degree-three monomials generated by $f_{\mathrm Q}$ from each quadratic coordinate.}
\label{tab:cubic_generation}\\
\toprule
Quadratic coordinate & Distinct cubic monomials in $\LieQ q$\\
\midrule
\endfirsthead
\toprule
Quadratic coordinate & Distinct cubic monomials in $\LieQ q$\\
\midrule
\endhead
""" + "\n".join(table_lines) + r"""
\bottomrule
\end{longtable}
"""
    (GENERATED_DIR / "cubic_generation_table.tex").write_text(cubic_table, encoding="utf-8")

    generating_rows: dict[Monomial, list[Monomial]] = defaultdict(list)
    for source, generated_map in m3_sources.items():
        for generated in generated_map:
            generating_rows[generated].append(source)
    shared = [(q, sources) for q, sources in generating_rows.items() if len(sources) > 1]
    shared.sort(key=lambda item: natural_key(item[0]))
    shared_lines: list[str] = []
    for q, sources in shared:
        source_text = " and ".join(
            rf"$\LieQ({format_monomial_tex(source)})$" for source in sources
        )
        shared_lines.append(rf"${format_monomial_tex(q)}$ & {source_text} \\")
    shared_row_text = "% Generated by scripts/generate_example_artifacts.py\n" + "\n".join(shared_lines) + "\n"
    (GENERATED_DIR / "shared_cubic_rows.tex").write_text(shared_row_text, encoding="utf-8")
    shared_table = r"""% Generated by scripts/generate_example_artifacts.py
\begin{center}
\begin{tabular}{@{}p{0.25\textwidth}p{0.65\textwidth}@{}}
\toprule
Shared cubic coordinate & Generating scalar derivatives\\
\midrule
""" + "\n".join(shared_lines) + r"""
\bottomrule
\end{tabular}
\end{center}
"""
    (GENERATED_DIR / "shared_cubic_table.tex").write_text(shared_table, encoding="utf-8")

    family_order = ["SII", "SIE", "SEE", "SSI", "SSE"]
    closure_lines: list[str] = []
    for fam in family_order:
        seeds_count = sum(1 for q in m3_seeds if family(q) == fam)
        final_count = sum(1 for q in m3 if family(q) == fam)
        closure_lines.append(
            rf"${fam}$ & {seeds_count} & {final_count - seeds_count} & {final_count} \\"
        )
    closure_lines.append(r"\midrule")
    closure_lines.append(
        rf"Total & {len(m3_seeds)} & {len(m3 - m3_seeds)} & {len(m3)} \\"
    )
    closure_row_text = "% Generated by scripts/generate_example_artifacts.py\n" + "\n".join(closure_lines) + "\n"
    (GENERATED_DIR / "closure_family_rows.tex").write_text(closure_row_text, encoding="utf-8")
    closure_table = r"""% Generated by scripts/generate_example_artifacts.py
\begin{center}
\begin{tabular}{@{}lrrr@{}}
\toprule
Family & Quadratic seeds & Added by closure & Final count\\
\midrule
""" + "\n".join(closure_lines) + r"""
\bottomrule
\end{tabular}
\end{center}
"""
    (GENERATED_DIR / "closure_family_table.tex").write_text(closure_table, encoding="utf-8")

    dictionary_lines: list[str] = []
    for index_value, q in enumerate(sorted(m3, key=natural_key), start=1):
        dictionary_lines.append(
            rf"{index_value} & {family(q)} & ${format_monomial_tex(q)}$ & {seed_origin(q, m3_seeds)} \\"
        )
    dictionary_row_text = "% Generated by scripts/generate_example_artifacts.py\n" + "\n".join(dictionary_lines) + "\n"
    (GENERATED_DIR / "m3_dictionary_rows.tex").write_text(dictionary_row_text, encoding="utf-8")
    dictionary_table = r"""% Generated by scripts/generate_example_artifacts.py
\begin{longtable}{@{}rlll@{}}
\caption{Complete 67-element cubic dictionary $\mathcal M_3^{\mathcalE}$.}
\label{tab:complete_m3_dictionary}\\
\toprule
Index & Family & Monomial & Origin\\
\midrule
\endfirsthead
\toprule
Index & Family & Monomial & Origin\\
\midrule
\endhead
""" + "\n".join(dictionary_lines) + r"""
\bottomrule
\end{longtable}
"""
    (GENERATED_DIR / "m3_dictionary_table.tex").write_text(dictionary_table, encoding="utf-8")


def verify() -> dict[str, int]:
    m2_seeds = {monomial([("S", i), ("I", j)]) for i, j in EDGES}
    m2 = linear_closure(m2_seeds)
    m3_seeds, m3_sources = generate_next_degree(m2)
    m3 = linear_closure(m3_seeds)
    m4_seeds, _ = generate_next_degree(m3)
    m4 = linear_closure(m4_seeds)

    observed = {
        "channels": len(EDGES),
        "M2 seeds": len(m2_seeds),
        "M2": len(m2),
        "raw cubic appearances": sum(len(records) for records in m3_sources.values()),
        "M3 seeds": len(m3_seeds),
        "M3 closure additions": len(m3 - m3_seeds),
        "M3": len(m3),
        "dim z2": 12 + len(m2),
        "dim z3": 12 + len(m2) + len(m3),
        "M4 seeds": len(m4_seeds),
        "M4": len(m4),
    }
    expected = {
        "channels": 7,
        "M2 seeds": 7,
        "M2": 14,
        "raw cubic appearances": 51,
        "M3 seeds": 42,
        "M3 closure additions": 25,
        "M3": 67,
        "dim z2": 26,
        "dim z3": 93,
        "M4 seeds": 159,
        "M4": 223,
    }
    if observed != expected:
        raise AssertionError((observed, expected))

    if not all(linear_generated_terms(q) <= m2 for q in m2):
        raise AssertionError("The degree-two dictionary is not linearly closed.")
    if not all(linear_generated_terms(q) <= m3 for q in m3):
        raise AssertionError("The degree-three dictionary is not linearly closed.")
    if not all(degree(q) == 3 for q in m3):
        raise AssertionError("The degree-three dictionary contains a non-cubic monomial.")
    if not all(degree(q) == 4 for q in m4):
        raise AssertionError("The degree-four dictionary contains a non-quartic monomial.")

    write_csvs(m2_seeds, m2, m3_seeds, m3, m3_sources, m4_seeds, m4)
    write_generated_tex(m2, m3_seeds, m3, m3_sources, m4_seeds, m4)
    return observed


def main() -> None:
    observed = verify()
    for key, value in observed.items():
        print(f"{key}: {value}")
    print("All three-city Algorithm 1 checks passed.")
    print(f"CSV outputs: {DATA_DIR}")
    print(f"Generated TeX: {GENERATED_DIR}")


if __name__ == "__main__":
    main()
