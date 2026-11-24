"""Check the public reproducibility map against the packaged repository.

This is a metadata/traceability check, not a scientific numerical substitute.
It checks the printed manuscript labels and existence of source/output files;
author-drawn TikZ schematic Figure 1 is outside this numerical software scope.
"""
from pathlib import Path
import json
import re
import csv

ROOT = Path(__file__).resolve().parents[1]
MAPPING = ROOT / "doc/reproducibility_map.json"
GUIDE = ROOT / "doc/REPRODUCIBILITY_INDEX.md"


def main():
    raw = json.loads(MAPPING.read_text(encoding="utf8"))
    entries = raw["items"]
    expected = [f"Table {n}" for n in range(2, 10)] + [f"Figure {n}" for n in range(2, 6)]
    assert [x["item"] for x in entries] == expected, "Missing, duplicate, or out-of-order figure/table ID"
    contents = GUIDE.read_text(encoding="utf8")
    for row in entries:
        assert row["latex_label"] in contents, row["latex_label"]
        assert row["entrypoint"] in contents, row["entrypoint"]
        assert row["outputs"] and row["inputs"], row["item"]
        for p in row["inputs"] + row["outputs"]:
            q = ROOT / p
            assert q.is_file(), f"{row['item']}: missing packaged source/output: {p}"
            assert str(q.resolve()).startswith(str(ROOT.resolve()) + '/'), "Unexpected external path"
    with (ROOT / "output/data/sparse_random_realizations.csv").open(newline="") as f:
        trials = list(csv.DictReader(f))
    assert len(trials) == 250
    assert sorted({int(r["n"]) for r in trials}) == [25, 50, 100, 200, 500]
    for n in (25, 50, 100, 200, 500):
        rows = [r for r in trials if int(r["n"]) == n]
        assert len(rows) == 50 and {int(r["realization"]) for r in rows} == set(range(50))
        assert len({int(r["seed"]) for r in rows}) == 50
    with (ROOT / "experiments/data/workplace_topology.csv").open(newline="") as f:
        work = list(csv.DictReader(f))
    seeds = sorted(int(r["seed"]) for r in work if r["type"] == "synthetic")
    assert seeds == list(range(20261112, 20261142)), "Workplace seeds do not match declared interval"
    with (ROOT / "experiments/data/workplace_summary.json").open() as f:
        summary = json.load(f)
    assert summary["synthetic_seeds"] == seeds
    assert (ROOT / ".python-version").read_text().strip() == '3.13.5'
    assert (ROOT / "requirements-lock.txt").is_file()
    print("REPRODUCIBILITY_INDEX_PASS: 8 numerical tables, 4 data-derived figures, all listed packaged paths, 250 accepted graph seeds, 30 workplace seeds, Python/dependency references")


if __name__ == "__main__":
    main()
