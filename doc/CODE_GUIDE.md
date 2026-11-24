# Guide to the Python implementation

This guide is intended for readers who want to inspect or modify the numerical
study, rather than merely rerun a command. The baseline and synthetic comparison networks use illustrative,
nondimensional SEIR parameters. The additional benchmark additionally uses measured
face-to-face *contact observations* from the public SocioPatterns InVS dataset,
aggregated into a fixed network with assumed transmission weights; it is not a
calibrated epidemic dataset. A receiving-row matrix convention is used
throughout: `A[i,j] > 0` means that infectious population `j` contributes to
infection pressure at susceptible population `i`.

## Source of the numerical model

In `scripts/seir_network.py`, each node follows a local SEIR system. The
nonlinear infection pressure is `beta * S * (A @ I)`; exposed individuals
progress to infectious at rate `sigma` and infectious individuals leave that
compartment at rate `gamma`. The local sum `S+E+I+R` is invariant because no
terms move compartmental mass between nodes. The ODE solver integrates the
*original* nonlinear system, not the lifted approximation.

The `graph_topologies.py` module builds reciprocal path and star graphs as
well as directed sparse-random graphs; each node also has an aggregate
within-population diagonal channel. The random ensemble uses the explicitly
recorded `default_rng` stream and an admission rule ensuring that node 1
has an outgoing off-diagonal channel. Changing this rule changes the sampled
ensemble and therefore the manuscript statistics.

`lifting_metrics.py` constructs a dictionary of commutative monomials. At
quadratic order, the supported observables are `S_i I_j` and `S_i E_j` for
active channels. Quadratic transmission generates cubic seeds; repeated
replacement of infectious factors by exposed ones closes the dictionary under
the linear compartmental transitions. Repeated factors are retained, while
commutative duplicates are combined. The support-reachable Carleman comparison
has the same dictionary under these rules; it is not a distinct speedup.

`residuals.py` differentiates the retained quadratic observables along the
original ODE. It returns the Euclidean norm of the omitted cubic forcing,
not an error between two predicted trajectories. Its first-closure bound is
computed from weighted incoming transmission intensity.

## Original results and plots

- `scripts/config.py` collects all experimental constants. To change the
  scientific scenario, modify this file and rebuild *all* output files.
- `scripts/run_experiments.py` calculates topology counts, cubic dictionary
  sizes, sampled network seeds, original/normalized-weight trajectories,
  peak/average residuals, and numerical-state checks.
- `scripts/peak_grid_sensitivity.py` reruns the ten frozen cases at two
  different output spacings. It does not read the archived CSV. The original
  v1.0.2 values survive only as a read-only regression fixture.
- `scripts/make_tables.py`, `scripts/make_figures.py` transform the generated
  CSVs into the original LaTeX tables and vector PDF figures.
- `scripts/validate_outputs.py`, `validate_manuscript_alignment.py` check the
  mathematical interpretation and reported output conventions.

## Revised experiments

- `structural_benchmarks.py`: computes full ordered and symmetric dimensions
  from binomial coefficients. It **does not** assemble the massive matrices.
- `graph_residual_bounds.py`: reconstructs all 52 original contact supports under two
  weighting rules, evaluates the refined analytical bound channel by channel,
  checks it against observed peaks, then averages realization-level ratios.
- `source_sensitivity.py`: moves the original localized infection to another
  node. Its RMS statistic is the Euclidean residual divided by `sqrt(2*m)`;
  the infinity norm is also saved for every controlled scenario.
- `dictionary_performance.py`: measures construction of degree-three
  dictionaries in isolated interpreter processes. Each timing is specific to
  the machine; the dictionary dimensions are exact.
- `sparse_operator.py`: constructs `K_2` and `K_3` as CSR matrices. It
  assembles each row by differentiating the retained monomial, merges duplicate
  coefficients, and compares its vector field with direct Lie derivatives on
  small networks before reporting larger matrix sizes and storage.
- `large_networks.py`: generates larger *synthetic* paths and random
  networks with fixed seeds. These observations are finite-range measurements,
  not proof of a uniform-degree asymptotic bound for random graphs.
- `peak_grid_check.py`: tests the newly generated coarse/fine residual
  peaks against the immutable v1.0.2 reference; it does not produce input data.
- `make_dimension_figure.py` and `make_experiment_tables.py`: build the
  revised figure and LaTeX fragments from the newly computed benchmark CSVs.
- `theory_tests/`: checks graph-induced vs generator-reachable monomial sets
  and validates the finite-order analytic bounds using rational arithmetic.

The documented entry point is `scripts/reproduce_all.py`. It builds the entire
experiment in dependency order and stops at the first failed check. The output
files named in `experiments/README.md` are the scientific
record; do not change them manually. Regenerated figures and tables should be
reviewed in the manuscript before publication.

## Where numerical agreement is expected

Exact integers (channel and monomial counts, dimensions and matrix nonzeros)
should match on all machines. Floating-point trajectories are tested with
reported tolerances rather than hashes. The manuscript includes results from
one reference execution; alternative machines will produce different wall
clock timings and peak RSS values. These differences do not imply a change in
scientific model or graph support.

## additional: comparable Carleman implementations

`experiments/scripts/carleman_operators.py` holds **one** shared sparse
operator assembler and the three basis-selection policies. Keeping assembly
identical isolates basis-selection overhead and avoids conflating basis size
with numerical implementation. `carleman_cost_comparison.py` is the execution
entry point. All three methods treat monomials as commutative with repeated
factors retained; no permutation duplicates enter the symmetric benchmark.

`sociopatterns_workplace.py` reads and verifies the original CC0 SocioPatterns
InVS workplace sensor archive (`t i j` in 20-second windows). It counts
unique observed pairs and aggregate durations and uses two *illustrative*
positive edge-weight conventions. The undirected contact union is converted
to reciprocal directed effective channels; one positive diagonal model channel
is assumed per node, as in the submitted SEIR model, but the source data do
not measure self-contacts. A fixed incoming intensity normalization is then
applied. The script compares its degree-three dictionary and illustrative
closure-residual peaks with 30 fixed-seed G(92,755) graphs. A daily observation
count is reported, but the time-stamped contact sequence is not used to
calibrate or integrate a temporal-contact SEIR model. See the source-data
provenance file and accompanying CSV/JSON summaries.


`truncation_accuracy.py` computes finite-horizon approximation errors with an
independent high-accuracy SEIR ODE solver and sparse matrix exponential.
Errors may increase from one truncation degree to another, so monotonicity
and asymptotic convergence are deliberately **not** asserted.

## Verifying the numbers printed in the manuscript

`python scripts/validate_reported_tables.py` checks every numerical cell in
eight scientific tables against the regenerated CSVs (144 numeric values in
the current manuscript). The repository contains a **frozen transcription**
of the approved `05_numerics.tex` table rows in
`experiments/reference/manuscript_table_snapshot.json`; this reference
is not computed from the CSVs under test. When preparing the journal files,
verify the actual LaTeX source rather than only this archive snapshot:

```bash
python scripts/validate_reported_tables.py --manuscript /path/to/manuscript
```

The check uses the decimal precision actually displayed in each table. For
the cost comparison, reference times are medians of the fixed recorded run in
`experiments/reference/carleman_costs_reference.csv`. New
runtime measurements are **not** required to match those times; only the basis
dimensions and CSR storage are required to coincide. The reference CSV is an
archived observation, not an extra computational input or a second source of
theoretical results.

If the manuscript is edited, regenerate the frozen transcription only after
checking its table values independently. Do not bypass a failed comparison by
copying the CSV into the snapshot. This checker does not replace mathematical
verification or review of narrative claims in the text.
