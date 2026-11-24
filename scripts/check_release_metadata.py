"""Validate GitHub/Zenodo metadata for the 1.0.4 release source archive.

No DOI is fabricated: the new version-specific DOI is available only after
Zenodo archives the release. Use --require-published only after that event.
"""
from __future__ import annotations
import argparse
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GITHUB = "https://github.com/ebaeyens/repository-graph-induced-seir-lifting"
VERSION = "1.0.4"
DOI_102 = "10.5281/zenodo.21427810"
DOI_103 = "10.5281/zenodo.22080488"
DOI_PATTERN = re.compile(r"10\.5281/zenodo\.\d+")


def check(manuscript: Path | None, require_published: bool) -> None:
    def read(path: str) -> str:
        return (ROOT / path).read_text(encoding="utf-8")

    if (ROOT / "zenodo.json").exists():
        raise AssertionError("Wrong metadata filename: use .zenodo.json, not zenodo.json")
    if not (ROOT / ".zenodo.json").is_file():
        raise AssertionError("Missing GitHub/Zenodo-recognized .zenodo.json file")

    metadata = json.loads(read(".zenodo.json"))
    readme, cff, bib, notes = [read(p) for p in
                               ("README.md", "CITATION.cff", "CITATION.bib", "RELEASE_NOTES.md")]
    if metadata.get("version") != VERSION:
        raise AssertionError("Zenodo version is not 1.0.4")
    if metadata.get("upload_type") != "software" or metadata.get("license", "").upper() != "MIT":
        raise AssertionError("Zenodo software type or license invalid")
    if not metadata.get("creators"):
        raise AssertionError("Zenodo creator list empty")
    for name, content in (("README",readme),("CFF",cff),("BibTeX",bib),("Release notes",notes)):
        if VERSION not in content:
            raise AssertionError(f"{name} is not versioned consistently as {VERSION}")
    if cff.count('version: "'+VERSION+'"') != 1:
        raise AssertionError("CFF version inconsistent")
    if f"version = {{{VERSION}}}" not in bib:
        raise AssertionError("BibTeX version inconsistent")
    if 'repository-code: "'+GITHUB+'"' not in cff or 'url = {'+GITHUB+'}' not in bib:
        raise AssertionError("Software citation URL inconsistent")
    if not any(r.get("identifier") == GITHUB for r in metadata.get("related_identifiers", [])):
        raise AssertionError("Zenodo GitHub URL missing")
    if GITHUB not in readme:
        raise AssertionError("README missing public GitHub URL")
    for name, content in (("README", readme), ("Zenodo",json.dumps(metadata)),("Release notes",notes)):
        if DOI_102 not in content or DOI_103 not in content:
            raise AssertionError(f"{name} omits predecessor identifiers")
    for name, content in (("README",readme),("CFF",cff),("BibTeX",bib),("Zenodo",json.dumps(metadata))):
        if "enrbae" in content or '1.0.4-rc' in content:
            raise AssertionError(f"{name} contains stale repository/release identifiers")
    if "Figures 2–5" not in readme:
        raise AssertionError("README must identify only numerical figures 2–5")
    if not (ROOT / "doc/REPRODUCIBILITY_INDEX.md").is_file():
        raise AssertionError("No public table-by-table numerical reproduction index")
    if "SocioPatterns" not in read("doc/CODE_GUIDE.md"):
        raise AssertionError("Data source omitted")

    manuscript_text = None
    if manuscript is not None:
        source = manuscript / "manuscript.tex" if manuscript.is_dir() else manuscript
        manuscript_text = source.read_text(encoding="utf-8")
        if DOI_102 not in manuscript_text:
            raise AssertionError("Manuscript missing historical DOI")

    if require_published:
        release_doi = metadata.get("doi", "")
        if (not DOI_PATTERN.fullmatch(release_doi) or
                release_doi in {DOI_102, DOI_103}):
            raise AssertionError("The 1.0.4 Zenodo DOI must be confirmed after archiving")
        for label, content in (("README",readme),("CFF",cff),("BibTeX",bib)):
            if release_doi not in content:
                raise AssertionError(f"{label} does not contain the verified 1.0.4 DOI")
        if manuscript_text is not None and release_doi not in manuscript_text:
            raise AssertionError("Submitted manuscript missing the actual 1.0.4 DOI")
    else:
        if metadata.get("doi") or re.search(r'^doi:', cff, re.M):
            raise AssertionError("Do not preassign an unverified version DOI")
    print("RELEASE_METADATA_PASS", VERSION, "require published DOI:", require_published)


if __name__ == "__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manuscript", type=Path)
    parser.add_argument("--require-published", action="store_true")
    args=parser.parse_args()
    check(args.manuscript,args.require_published)
