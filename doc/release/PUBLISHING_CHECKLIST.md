# GitHub and Zenodo publication checklist for v1.0.2

## Repository preparation

- [x] Repository scope limited to the numerical illustrations in Section 5.
- [x] Standalone worked examples excluded from this release.

- [x] Version updated to `v1.0.2`.
- [x] Terminology and notation aligned with the final manuscript.
- [x] Structural outputs and scientific values validated as unchanged.
- [x] `pytest` tests and output validation pass.
- [x] Python caches and build artifacts removed.
- [x] Release notes updated.

## GitHub release

- [ ] Commit the final files to the release branch.
- [ ] Merge or push the intended release commit to GitHub.
- [ ] Create and push annotated tag `v1.0.2`.
- [ ] Create the GitHub release from exactly that tag.

## Zenodo version

- [ ] Create a new version from the existing Zenodo record.
- [ ] Reserve the new version DOI before publication.
- [ ] Insert the reserved DOI into `CITATION.cff`, `CITATION.bib`, and `README.md`.
- [ ] Confirm that the Zenodo archive matches GitHub tag `v1.0.2`.
- [ ] Publish the Zenodo version and verify DOI resolution.

## Manuscript

- [ ] Replace the v1.0.1 software citation with v1.0.2 and its new DOI only if
      the manuscript has not yet been submitted or the editor permits the update.
- [ ] Otherwise retain the reproducible v1.0.1 citation and document v1.0.2 as
      a later synchronization release.
