"""Check terminology and citation anchors (numeric tables have a separate validator)."""
from __future__ import annotations

import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FORBIDDEN = ("mechanistic", "mechanistically", "linear closure", "linear_closure")


def scan_text_tree(base: Path) -> list[str]:
    """Read repository text files for terminology and consistency checks."""
    issues: list[str] = []
    allowed_suffixes = {".py", ".md", ".tex", ".csv", ".txt", ".cff", ".bib", ".json", ".yml", ".yaml"}
    for path in base.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in allowed_suffixes:
            continue
        if path.name in {"RELEASE_NOTES.md", "RELEASE_VALIDATION_REPORT.md", "RELEASE_INSTRUCTIONS.md", "validate_manuscript_alignment.py"}:
            continue  # historical terms or validation constants are intentional
        text = path.read_text(encoding="utf-8", errors="ignore").lower()
        for term in FORBIDDEN:
            if term in text:
                issues.append(f"{path.relative_to(base)}: forbidden term {term!r}")
    return issues


def validate_manuscript(manuscript: Path) -> list[str]:
    """Check whether repository conventions agree with the manuscript source."""
    issues: list[str] = []
    combined = "\n".join(
        p.read_text(encoding="utf-8", errors="ignore")
        for p in manuscript.rglob("*.tex")
    )
    expected = [
        "fig:dimension_comparison",
        "fig:higher_order_dictionary_size",
        "10.5281/zenodo.21427810",
    ]
    for item in expected:
        if item not in combined and item not in (manuscript / "references.bib").read_text(encoding="utf-8", errors="ignore"):
            issues.append(f"manuscript expectation not found: {item}")
    return issues


def main() -> None:
    """Run this module as a command-line program and report its completed
    checks.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("--manuscript", type=Path)
    args = parser.parse_args()
    issues = scan_text_tree(ROOT)
    if args.manuscript:
        issues.extend(validate_manuscript(args.manuscript.resolve()))
    if issues:
        raise SystemExit("\n".join(issues))
    print("Repository terminology and manuscript citation-anchor checks passed; use validate_reported_tables.py for numeric table alignment.")


if __name__ == "__main__":
    main()
