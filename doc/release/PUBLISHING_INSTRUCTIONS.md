# Publishing v1.0.3 on GitHub and Zenodo

The version-specific DOI has already been reserved:

`10.5281/zenodo.22080488`

Release `v1.0.3` is documentation- and citation-metadata only. Do not modify
scientific code, numerical parameters, seeds, generated outputs, tables, or
figures while preparing this release.

## 1. Commit and tag on GitHub

```bash
git checkout -b release/v1.0.3
git add .
git commit -m "Release v1.0.3: correct citation and repository metadata"
git push -u origin release/v1.0.3
```

After review, merge or fast-forward the release commit to the intended default
branch. Then create the annotated tag from the exact release commit:

```bash
git tag -a v1.0.3 -m "Version 1.0.3"
git push origin v1.0.3
```

Create the GitHub release from tag `v1.0.3`, using `RELEASE_NOTES.md` as the
release description.

## 2. Complete the Zenodo version

1. Open the already-created new-version draft.
2. Confirm that the reserved DOI is `10.5281/zenodo.22080488`.
3. Confirm that version is `1.0.3` and the repository link points to
   `https://github.com/ebaeyens/repository-graph-induced-seir-lifting`.
4. Upload or let the GitHub–Zenodo integration archive exactly tag `v1.0.3`.
5. Check the draft file list and metadata before publishing.
6. Publish the Zenodo version and verify that <https://doi.org/10.5281/zenodo.22080488>
   resolves to it.

## 3. CNSNS manuscript citation

Before submission, update the manuscript, bibliography, Data and Code
Availability statement, and cover letter so that all of them cite release
`v1.0.3` using DOI `10.5281/zenodo.22080488`.
