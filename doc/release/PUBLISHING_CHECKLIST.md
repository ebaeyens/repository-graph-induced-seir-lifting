# GitHub and Zenodo publication checklist for v1.0.3

## Repository preparation

- [x] Version updated to `v1.0.3`.
- [x] Reserved Zenodo DOI recorded as `10.5281/zenodo.22080488`.
- [x] Repository links updated to `https://github.com/ebaeyens/repository-graph-induced-seir-lifting`.
- [x] Citation metadata synchronized.
- [x] `zenodo.json` renamed to `.zenodo.json`.
- [x] Scientific code and generated numerical outputs preserved from `v1.0.2`.
- [x] Release notes and release documentation updated.

## Validation

- [x] Run `python -m pytest -q` (`1 passed`).
- [x] Run `python scripts/validate_outputs.py` (passed).
- [x] Run `python scripts/validate_manuscript_alignment.py` (passed).
- [x] Confirm protected-file checksums match `v1.0.2` (37/37 unchanged).
- [x] Confirm there are no obsolete repository-owner links or DOI-pending
      placeholders.

## GitHub release

- [ ] Commit the final files to the intended release branch.
- [ ] Merge or fast-forward the release commit to the intended default branch.
- [ ] Create and push annotated tag `v1.0.3`.
- [ ] Create the GitHub release from exactly that tag.

## Zenodo version

- [x] Create the new Zenodo version draft.
- [x] Reserve DOI `10.5281/zenodo.22080488`.
- [ ] Upload or archive exactly GitHub tag `v1.0.3`.
- [ ] Confirm the Zenodo draft metadata shows version `1.0.3`.
- [ ] Publish the Zenodo version.
- [ ] Verify DOI resolution after publication.

## CNSNS manuscript

- [ ] Replace the `v1.0.2` software citation and DOI with `v1.0.3` and
      `10.5281/zenodo.22080488` before submission.
- [ ] Verify the Data and Code Availability statement and cover letter use the
      same version and DOI.
