# Release validation report — v1.0.2

## Scope

This release aligns the repository with the final manuscript terminology,
notation, figure numbering, documentation, tests, and metadata. The numerical
model, experimental configuration, random seeds, and reported scientific
results are unchanged.

## Six completed phases

1. **Baseline and preservation**
   - inventoried the original repository;
   - retained the previous manuscript-supported DOI
     `10.5281/zenodo.21427751` as the v1.0.1 reference;
   - compared all stored CSV values before and after the update.

2. **Terminology and notation propagation**
   - replaced procedural *linear closure* with *linear saturation*;
   - retained *linearly closed* for the resulting property;
   - retained *first edge-closure lifting* as the established name;
   - removed *mechanistic* terminology.

3. **Documentation and metadata update**
   - updated README figure references and figure layout descriptions;
   - updated release notes, publishing checklist, CFF, BibTeX, and Zenodo
     metadata to v1.0.2;
   - left the v1.0.2 DOI pending until Zenodo reserves the new version DOI.

4. **Regeneration and scientific validation**
   - regenerated structural CSVs, LaTeX tables, and PDF figures;
   - confirmed that every numerical CSV value matches the previous release,
     after accounting only for renamed terminology columns;
   - `scripts/validate_outputs.py` passes.

5. **Testing and cleanup**
   - converted quick checks into discoverable pytest tests;
   - added `scripts/validate_manuscript_alignment.py`;
   - removed Python caches and LaTeX auxiliary files;

6. **Release packaging**
   - prepared a clean v1.0.2 repository tree for GitHub;
   - added publication instructions and DOI reservation steps.

## Validation results

- `python -m pytest -q`: **1 passed**
- `python scripts/validate_outputs.py`: **passed**
- `python scripts/validate_manuscript_alignment.py --manuscript <path>`:
  **passed**
- all stored numerical CSV values: **unchanged**

## DOI status

The manuscript currently cites v1.0.1 using DOI
`10.5281/zenodo.21427751`. Release v1.0.2 requires a new version-specific DOI.
After reserving it in Zenodo, insert it into `CITATION.cff`, `CITATION.bib`, and
`README.md` before publishing the Zenodo version.
