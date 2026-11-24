# Reproducing the original and revised SEIR experiments

The scripts in this directory accompany the manuscript
**CNSNS-D-26-05035**. They extend the scientific baseline v1.0.2 (DOI: 10.5281/zenodo.21427810).
The intervening public v1.0.3 release (DOI 10.5281/zenodo.22080488)
updated documentation/metadata only. The additional numerical experiments
are part of **version 1.0.4**, not of v1.0.2 or v1.0.3.
The manuscript source remains a separate component; the CSVs, figure PDFs,
regression tests and their generating Python programs are included here.

## Complete reproduction

From the repository root, create an environment and run:

```bash
python3.13 -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\Activate.ps1
python -m pip install -r requirements-lock.txt
python -m pip install -r requirements-dev.txt
python scripts/reproduce_all.py
make check
```

The driver first **cleans all generated outputs**, runs the original dynamics,
structural and peak-grid experiments, and then executes the additional numerical experiments
in dependency order. It generates all CSVs and the PDF figure for the
dimensional comparison. The additional LaTeX table fragments are built from CSV data,
not transcribed by hand. The command fails immediately if a stage or numerical
validation fails. It does **not** fetch datasets or read unpublished files.

Software versions used for this reference execution are defined by
`.python-version` (Python 3.13.5) and `requirements-lock.txt`.
SciPy uses `solve_ivp`/RK45 (`rtol=1e-8`, `atol=1e-10`) with 3201
regular samples on [0,480]. NumPy `default_rng` currently uses PCG64;
master seed 12345 gives the per-size stream seed `12345+n`. Admissible
realization seeds are stored in `output/data/` and reused between weighting
schemes. This is a deterministic numerical study, not disease-specific data
calibration. Rerunning with different library versions can change last digits
of the trajectories.

## Table and figure entry points

The **complete, verified, numbered map** is
[`doc/REPRODUCIBILITY_INDEX.md`](../doc/REPRODUCIBILITY_INDEX.md), with
individual commands and input/output filenames for Tables 2–9 and data-derived Figures 2–5.
Run `python scripts/check_reproducibility_index.py` to verify the paths and
coverage. The shorter stage overview below provides additional context, but
is not the manuscript-numbered index.

## Artifact map

| Revised result | Generating program | Output |
|---|---|---|
| Original topology, dimension, cubic dictionaries, dynamic residuals | `scripts/run_experiments.py`, `scripts/make_tables.py`, `scripts/make_figures.py` | `output/{data,tables,figures}/` |
| Original coarse/fine peak comparison | `scripts/peak_grid_sensitivity.py` | `output/data/peak_grid_sensitivity.csv` |
| Independent check against frozen v1.0.2 peaks | `peak_grid_check.py` | `experiments/data/peak_grid_refinement_check.csv` |
| Complete ordered and symmetric dimensions, reachable support counts | `structural_benchmarks.py` | `experiments/data/structural_benchmarks.csv` |
| Revised Figure 2 | `make_dimension_figure.py` | `experiments/figures/figure_2_dimension_comparison.pdf` |
| Graph-dependent residual bounds, all 104 cases | `graph_residual_bounds.py` | `refined_residual_summary.csv`, `refined_bounds_by_realization.csv` |
| Alternative source-node initial conditions and RMS | `source_sensitivity.py` | `source_node_sensitivity.csv`, `random_normalized_rms.csv` |
| Cubic dictionary construction timing and memory | `dictionary_performance.py` | `dictionary_build_runs.csv`, `dictionary_build_summary.csv` |
| Sparse degree-two/three operator construction | `sparse_operator.py` | `sparse_operator_costs.csv` |
| 1,000–2,000-node synthetic networks | `large_networks.py` | `large_networks.csv`, `large_networks_summary.csv` |
| Revised manuscript table fragments | `make_experiment_tables.py` | `experiments/tables/*.tex` |
| Exact symbolic equality and bound checks | `theory_tests/*.py` | JSON/console checks |
| Final data validation | `validate_experimental_data.py`, `scripts/validate_outputs.py` | Error if a required relation fails |

Unless a full path is shown, outputs belong to `experiments/data/`.
The check of the original peak grid compares the *freshly generated* CSV to an
immutable copy of the published reference in `experiments/reference/`;
that reference is not used by the peak-grid generator.

## Interpretation and limitations

- `A[i,j]` denotes a transmission channel from infectious source `j` to
  susceptible receiving node `i`; diagonal channels represent local aggregate
  transmission. Unit weights and fixed incoming intensity use the same support.
- The Carleman ordered and symmetric dimensions are analytical counts. No
  large, full dense Carleman matrices were assembled or timed. The reachable
  monomial-support benchmark is **equivalent** to the graph-induced support
  for the specified SEIR construction; no artificial speedup is claimed.
- Only degree-two and degree-three sparse operator construction is timed.
  Wall-clock timings and peak resident memory vary by hardware; the number
  of coordinates and nonzero entries do not.
- The larger networks are synthetic, not epidemiologically calibrated.
  Their finite-range scaling does not establish general asymptotics for
  unbounded-degree random network families.
- The new residual constants bound instantaneous omitted forcing. The
  projected trajectory-error theorem is separate and does not establish
  convergence as the truncation degree grows.

## Verification

The command `make check` runs unit tests and checks generated outputs. The
symbolic scripts use exact rational arithmetic when checking small networks.
The CSVs for time/memory are regenerated, but are *not* expected to be identical
on different machines. All other data are compared using appropriate exact
structural or numerical-tolerance checks.

If a run fails, consult the failing command printed by `reproduce_all.py`;
recheck versions before investigating tiny floating-point differences. Do not
change output CSVs or figures manually to make a test pass.

See also `doc/CODE_GUIDE.md` for an explanation of each algorithm and the
role of the input, output and validation files.

## Reproducible comparisons

The following scripts are run by `python scripts/reproduce_all.py` and are also
usable independently (all accept `--repo` and `--out`). They use the same
compartment order, oriented adjacency convention and SEIR parameters as the
submitted article. Their outputs are stored in `experiments/data/`.

- **`carleman_cost_comparison.py`**: compare degree-3 complete symmetric,
  full-Lie-generator-reachable and split-generated monomial supports on n=4,8,12
  path and star supports, with five repeated timings of **both** dictionary
  selection and the common sparse CSR assembler. `tracemalloc` reports Python
  allocation peaks, which are not the entire process RSS. CSR bytes count only
  matrix arrays. Timings are machine-dependent; comparisons with a different
  implementation or hardware must not be inferred. The reachable and split
  dictionaries and matrices are asserted identical.
- **`sociopatterns_workplace.py`**: read the supplied 2013 SocioPatterns InVS
  workplace 20-second face-to-face contact archive, aggregate it into a fixed
  contact support, and compare two positive weighting conventions against 30
  independently seeded G(92,755) graphs. Source file, CC0 license, DOI,
  orientation, diagonal model assumption, normalization and limitations are
  documented in `source_data/PROVENANCE.md`. The results contain dictionary
  dimensions, structural summaries, illustrative residual peaks and a daily
  count of contact records. The observed temporal contacts are **not** treated
  as empirical transmission rates, nor is the SEIR dynamics calibrated.

- **`truncation_accuracy.py`**: for a three-node path and star (which are isomorphic
  but differ in the initial infected node's role), integrate the original SEIR
  system on t=0..12, and compare original-coordinate errors of zero-input
  truncations of degree 2..5 initialized with the exact monomial lift.
  These results are finite-horizon diagnostics, **not a convergence theorem**.

Outputs: `carleman_costs.csv`, `workplace_topology.csv`,
`workplace_residuals.csv`, `workplace_daily_contacts.csv`,
`workplace_summary.json`, and `truncation_accuracy.csv`. All source data needed for these computations
are included with the release; no network access is required.
