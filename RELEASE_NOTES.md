# Software release 1.0.4

Version 1.0.4 accompanies the revised CNSNS manuscript. It extends the
scientific baseline v1.0.2 (DOI 10.5281/zenodo.21427810). The intervening
public release v1.0.3 (DOI 10.5281/zenodo.22080488) changed documentation
and citation metadata without altering the scientific outputs. Version 1.0.4
adds the numerical studies and reproducibility tools described below.

## Scientific additions

- Complete ordered and symmetric dimensions, and a documented equivalence to
  Carleman reachable monomial support (no claimed speedup over the latter).
- Computable graph-specific and prevalence-dependent residual bounds.
- Independent sparse degree-two/three operator assembly and numerical checks.
- Alternative initial infection locations and per-coordinate RMS diagnostics.
- Larger synthetic path and random network experiments (not calibrated disease data).
- Rebuilt output-grid sensitivity checks, with original archived data retained as
  a read-only regression fixture.
- Matched construction of the same degree-three operators for full
  symmetric, full-Lie-reachable and split-generated dictionaries, with five
  repetitions and identical CSR assembly.
- A documented SocioPatterns workplace face-to-face contact dataset (2013),
  compared with 30 size- and edge-matched synthetic networks; **not** a calibrated
  epidemiological contact network.
- Finite-horizon SEIR projection-error diagnostics at truncation degrees 2–5;
  the example does not show monotonic improvement beyond degree four.

## Reproducibility

The complete experimental workflow is available through `make reproduce-all`.
It regenerates original outputs and the additional review figures, tables,
numerical results and theoretical checks from an empty generated-output tree.
`make check` executes the tests and validators. The test workflow is also used
in continuous integration.

Run times and peak resident-memory values are observations from a particular
computer; they are not machine-independent regression targets.

## DOI and archival verification

GitHub release 1.0.4 is intended to be archived automatically by Zenodo in
the existing version series. The DOI for **this specific version** is provided
by the actual Zenodo record after processing. Do not use the older 1.0.2 or
1.0.3 DOIs for the new experiments. Once the record exists, verify its file
contents and DOI, and update the manuscript and software citation records.
