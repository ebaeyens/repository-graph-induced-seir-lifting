# Release validation report — v1.0.3

## Scope

Release `v1.0.3` corrects documentation, repository links, and citation
metadata in the archived `v1.0.2` tree. The numerical model, experimental
configuration, random seeds, scientific source code, generated outputs, and
reported scientific results are preserved unchanged.

## Metadata corrections

- release version updated to `v1.0.3`;
- release date updated to `2026-08-24`;
- reserved DOI recorded as `10.5281/zenodo.22080488`;
- repository URLs updated to `https://github.com/ebaeyens/repository-graph-induced-seir-lifting`;
- `zenodo.json` renamed to `.zenodo.json`;
- provisional DOI-pending language removed;
- citation metadata synchronized across README, CFF, BibTeX, and Zenodo JSON;
- manuscript-alignment validation updated to expect the `v1.0.3` DOI.

## Preservation requirement

The following material must remain byte-for-byte identical to `v1.0.2`:

- scientific Python implementation, except the metadata-only manuscript DOI
  expectation in `scripts/validate_manuscript_alignment.py`;
- all numerical CSV files;
- all generated LaTeX tables;
- all generated PDF figures;
- dependency files and numerical configuration.

## Validation results

- `python -m pytest -q`: **1 passed**;
- `python scripts/validate_outputs.py`: **passed**;
- `python scripts/validate_manuscript_alignment.py`: **passed**;
- protected-file checksum comparison against `v1.0.2`: **37/37 unchanged**;
- obsolete repository URLs, superseded DOI values, and DOI-pending placeholders:
  **none found**;
- `.zenodo.json`: **valid JSON**;
- `CITATION.cff`: **valid YAML**.
