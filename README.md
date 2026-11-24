# Graph-induced tensor liftings for networked SEIR models

This repository contains the Python code and generated numerical material for
Section 5 of the article:

> **Graph-Induced Tensor Liftings for Networked SEIR Models: Dimensional
> Reduction and Residual Analysis**

The code reproduces the data, LaTeX tables, and PDF figures used in the
numerical illustrations. It includes the original unit-weight experiment and a
complementary fixed-incoming-transmission-intensity comparison.

## Reproduce a specific table or figure

**[Table-by-table and figure-by-figure reproduction index](doc/REPRODUCIBILITY_INDEX.md)**
contains the exact entry points, prerequisites, CSV and PDF output paths, software
versions, PCG64/NumPy configuration and accepted random seeds for **Tables 2–9**
and **Figures 2–5** of the revised manuscript. Figure 1 is an author-drawn TikZ schematic, not a data-derived result. Its machine-readable counterpart
is `doc/reproducibility_map.json` and is checked by `make check-index`.

## Software and complete reproduction

This is software version **1.0.4**, extending the scientific baseline v1.0.2
(DOI 10.5281/zenodo.21427810). The intervening public version v1.0.3
(DOI 10.5281/zenodo.22080488) corrected documentation and citation metadata.
Version 1.0.4 contains the original experimental programs and additional
numerical studies supporting the revised article. Earlier published releases
remain unchanged. Zenodo assigns a distinct version DOI when the GitHub
1.0.4 release is archived; use that DOI when it becomes available.

To reproduce **all** results, run `make reproduce-all`, then
`make check`. The output directory and all additional generated files
are rebuilt without access to private local files. See
`experiments/README.md` for an item-by-item map, numerical
conventions, seeds, accuracy tolerances and interpretation limits.

For algorithm definitions, parameters, and input/output descriptions, see [`doc/CODE_GUIDE.md`](doc/CODE_GUIDE.md).
The numerical table validator compares 144 reported values in eight tables
against the accompanying CSV data. Run `make check-reported` to check these
values. Its optional `--manuscript` argument permits comparison with a supplied
copy of the article's LaTeX sources.

The comparable-cost, workplace-contact and truncation-accuracy experiments can also be reproduced independently using
`make reproduce-additional`. The full reproduction command
remains `make reproduce-all`; benchmark timing differences vary by machine.

## Repository structure

The repository includes `scripts/` for the SEIR simulations and reproduction
commands, `experiments/` for comparative benchmarks and observed-contact data,
`output/` for the original tables and figures, `tests/` for automated checks,
and `doc/` for descriptions of the algorithms and their inputs and outputs.
All these directories are included in the archive.


The generated `output/` directory is intentionally tracked.

## Scope of this repository

This repository is limited to the numerical illustrations reported in Section 5
of the associated article. Worked symbolic examples that are not part of those
numerical illustrations are maintained in separate repositories.

## Quick start

Create and activate a virtual environment, then install the dependencies:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

On Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

Reproduce and validate the original numerical outputs with:

```bash
python scripts/reproduce.py
```

or:

```bash
make reproduce
```

The structural and dynamic stages are executed separately to limit peak memory.
Runtime depends on the computer and numerical libraries.

## Generated results

The following list is an output-directory overview; for the **exact manuscript
figure/table mapping**, use `doc/REPRODUCIBILITY_INDEX.md`.


### Data

`output/data/` contains:

- `network_quantities.csv`: unit-weight channel counts and incoming-degree
  quantities for Table 2;
- `dimension_comparison.csv`: complete and graph-induced quadratic dimensions
  for Table 3 and Figure 2;
- `cubic_dictionary_size.csv`: quadratic and linearly closed cubic dictionary
  sizes for Table 6 and Figure 5;
- `sparse_random_realizations.csv`: seeds and raw support/dictionary quantities;
- `residual_sensitivity_summary.csv`: residual summaries for unit and normalized weights, including sample
  standard deviations of peak times;
- `residual_sensitivity_timeseries.csv`: both sets of residual curves and
  sparse-random pointwise standard-deviation bands;
- `sparse_random_residual_realizations.csv`: realization-level dynamic results
  for both weighting configurations;
- `simulation_validation.csv`: mass-conservation and nonnegativity audit;
- `residual_summary.csv` and `residual_timeseries.csv`: backward-compatible
  unit-weight subsets of the combined sensitivity outputs.

### Tables

`output/tables/` contains four LaTeX fragments:

- `network_quantities.tex`;
- `dimension_comparison.tex`;
- `residual_summary.tex`;
- `cubic_dictionary_size.tex`.

The residual results are presented in one compact table with two rows per
topology, and the random-ensemble peak-time standard deviation is reported.

### Figures

`output/figures/` contains:

- `dimension_comparison.pdf`;
- `residual_dynamics_unit.pdf`;
- `residual_dynamics_fixed_incoming_transmission_intensity.pdf`;
- `higher_order_dictionary_size.pdf`.

For Figure 2 in the revised manuscript, use `experiments/figures/figure_2_dimension_comparison.pdf`, not the legacy `output/figures/dimension_comparison.pdf`. Figure titles are not embedded in the PDFs; their descriptions belong to the manuscript captions. The residual PDFs appear separately as Figures 3 and 4 in the manuscript.
The unit-weight graph uses the window `[0, 240]` with an inset over
`[0, 20]`, while the fixed-incoming-transmission-intensity graph uses the full
window `[0, 480]` with an inset over `[0, 60]`.

## Numerical setup

The configuration in `scripts/config.py` matches Section 5:

- network sizes: 25, 50, 100, 200, and 500;
- dynamic simulations at `n = 100`;
- nondimensional SEIR parameters: `beta = 0.8`, `sigma = 0.25`,
  `gamma = 0.1`;
- time interval `[0, 480]` with 3201 output points, preserving the spacing
  `Delta t = 0.15`;
- localized initial condition `E_1(0) = I_1(0) = 10^{-3}`;
- one diagonal within-subpopulation transmission channel at every node;
- 50 directed sparse-random admissible realizations with off-diagonal probability
  `p = 4/n`; each accepted graph gives the initially infected node at least
  one off-diagonal outgoing transmission channel;
- master seed 12345, with the stream for size `n` initialized by `12345 + n`;
- peak-grid sensitivity output in `output/data/peak_grid_sensitivity.csv`.

The experiment is nondimensional and does not convert time or parameters to SI
units or a particular disease calendar.

## Weighting sensitivity

The dynamic experiment uses two configurations on the same supports:

1. **Unit weights:** every active diagonal and off-diagonal channel has weight
   one.
2. **Normalized weights:** every receiving row is rescaled
   according to

   ```text
   A_tilde[i, j] = A[i, j] / sum_k A[i, k]
   ```

   so `sum_j A_tilde[i, j] = 1` for every node.

The normalization includes diagonal channels, preserves the exact support, and
reuses the same random realizations, seeds, initial condition, parameters,
solver, tolerances, and output grid. Therefore the channel counts and all
graph-induced dictionary dimensions are identical in both cases; only the
trajectories, residuals, bounds, ratios, and peak-time statistics are
recomputed.

## Model and graph convention

The implemented model is

```text
dS_i/dt = -beta S_i sum_j a_ij I_j
dE_i/dt =  beta S_i sum_j a_ij I_j - sigma E_i
dI_i/dt =  sigma E_i - gamma I_i
dR_i/dt =  gamma I_i
```

`A[i, j]` represents the contribution of infectious individuals at source node
`j` to the infection pressure at receiving node `i`. The channels do not move
compartment populations between nodes. A positive diagonal entry represents
aggregate within-subpopulation transmission, not individual self-infection.
Each local population satisfies
`d(S_i + E_i + I_i + R_i)/dt = 0`.

## Graph-induced dictionaries

The degree-two dictionary contains `S_i I_j` and `S_i E_j` for every active
transmission channel. The degree-three dictionary is generated as in Algorithm
1 of the article:

1. generate the cubic seed set from the linearly closed degree-two dictionary
   through the quadratic transmission field;
2. canonicalize commutative monomials and merge duplicates;
3. saturate the cubic seed set under the linear SEIR transitions until no new
   same-degree monomial appears.

Repeated factors, such as `S_i I_i^2`, are retained.

## Running individual stages

```bash
python scripts/run_experiments.py --stage structural
python scripts/run_experiments.py --stage dynamic
python scripts/make_tables.py
python scripts/make_figures.py
python scripts/validate_outputs.py
```

Equivalent Make targets are `structural`, `dynamic`, `tables`, `figures`, and
`validate`.

To recreate empty output directories:

```bash
make clean-output
make reproduce
```

## Validation

`validate_outputs.py` checks:

- exact support preservation under row normalization;
- fixed total incoming transmission intensity in every row;
- unchanged first and representative cubic dictionary dimensions;
- unit-subset compatibility;
- realization counts and peak-time standard deviations;
- residual-bound consistency;
- final extinction-phase thresholds for the residual and active compartments;
- local mass conservation and numerical nonnegativity;
- required tables and figures;
- absence of embedded figure-title commands.

## Random-ensemble admission criterion

The initial condition is localized at node 1. Candidate directed random graphs
are generated from the deterministic seed stream and accepted only when node 1
has at least one off-diagonal outgoing channel. This criterion is declared
before simulation and prevents a structurally degenerate seed from being
trapped at its initial node. All accepted graph seeds are stored in
`output/data/sparse_random_realizations.csv`.

## Citation and license

The public baseline v1.0.2 is archived as DOI `10.5281/zenodo.21427810`.
Version 1.0.3 is archived as DOI `10.5281/zenodo.22080488`. The
version-specific DOI for 1.0.4 must be taken from its actual Zenodo record
after archiving the GitHub release. Do not cite an older release as if it
contained the additional experiments. Synchronize the verified DOI with
`CITATION.cff`, `CITATION.bib`, and the journal manuscript after publication.
GitHub–Zenodo metadata are provided in `.zenodo.json`.
The code is licensed under the MIT License as indicated in `LICENSE`.

- Development repository: <https://github.com/ebaeyens/repository-graph-induced-seir-lifting>
- Scientific baseline v1.0.2: <https://doi.org/10.5281/zenodo.21427810>
- Previous public release v1.0.3: <https://doi.org/10.5281/zenodo.22080488>

Citation metadata are provided in `CITATION.cff` and `CITATION.bib`.
The code is released under the MIT License. See `LICENSE`.

## SocioPatterns measured workplace contact benchmark

The revision adds the original CC0 SocioPatterns InVS 2013 workplace-contact
archive, verified by SHA-256. Run `make reproduce-additional` for the contact
analysis, matched Carleman comparison and finite-horizon error test. Run
`make reproduce-all` to rebuild the original and revised outputs in order.
The 92-participant and 755-pair network is *time-aggregated*: the study
examines fixed structural support, not real-time contact-driven epidemic
dynamics, nor clinical transmission data. Diagonal model channels are assumed,
not measured. See `experiments/source_data/PROVENANCE.md`.
