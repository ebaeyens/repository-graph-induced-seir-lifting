# Publishing v1.0.2 on GitHub and Zenodo

## 1. Commit and tag on GitHub

```bash
git checkout -b release/v1.0.2
git add .
git commit -m "Release v1.0.2: align repository with final manuscript"
git push -u origin release/v1.0.2
```

After review, merge or fast-forward the release commit to the intended default
branch. Then create the annotated tag from the exact release commit:

```bash
git tag -a v1.0.2 -m "Version 1.0.2"
git push origin v1.0.2
```

Create the GitHub release from tag `v1.0.2`, using `RELEASE_NOTES.md` as the
release description.

## 2. Create the Zenodo version

1. Open the existing Zenodo record and choose **New version**.
2. Reserve the DOI for the new version before publishing.
3. Insert the reserved DOI into:
   - `CITATION.cff` as `doi` and DOI `url`;
   - `CITATION.bib` as `doi` and DOI `url`;
   - the citation section of `README.md`.
4. Commit the DOI update and move/recreate the tag only if it has not yet been
   publicly released. Prefer reserving the DOI before the final GitHub tag.
5. Upload or let the GitHub–Zenodo integration archive exactly tag `v1.0.2`.
6. Publish the Zenodo version and verify that its files match the GitHub tag.

## 3. Manuscript citation

The current manuscript citation to v1.0.1 remains reproducible. Replace it by
v1.0.2 only before submission or when an editorial update is permitted, and
only after the new DOI has been published.
