# Graph-induced tensor liftings for networked SEIR models

This repository contains the Python code and generated numerical material for
Section 5 of the article:

> **Graph-Induced Tensor Liftings for Networked SEIR Models: Dimensional
> Reduction and Residual Analysis**

The code reproduces the data, LaTeX tables, and PDF figures used in the
numerical illustrations. It includes the original unit-weight experiment and a
complementary fixed-incoming-transmission-intensity comparison.

## Repository structure

```text
repository_graph_induced_seir_lifting/
├── README.md
├── LICENSE
├── CITATION.cff
├── requirements.txt
├── Makefile
├── doc/
│   └── release/
├── scripts/
│   ├── config.py
│   ├── graph_topologies.py
│   ├── seir_network.py
│   ├── residuals.py
│   ├── lifting_metrics.py
│   ├── run_experiments.py
│   ├── make_tables.py
│   ├── make_figures.py
│   ├── validate_outputs.py
│   └── reproduce.py
└── output/
    ├── data/
    ├── tables/
    └── figures/
```

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

Reproduce and validate all numerical outputs with:

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

### Data

`output/data/` contains:

- `network_quantities.csv`: unit-weight channel counts and incoming-degree
  quantities for Table 1;
- `dimension_comparison.csv`: complete and graph-induced quadratic dimensions
  for Table 2 and Figure 2;
- `cubic_dictionary_size.csv`: quadratic and linearly closed cubic dictionary
  sizes for Table 4 and Figure 5;
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

Figure titles are not embedded in the PDFs; their descriptions belong to the
manuscript captions. The residual PDFs appear separately as Figures 3 and 4 in the manuscript.
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

This repository is prepared as release `v1.0.2`, aligned with the final
manuscript terminology and documentation. The numerical outputs are unchanged
from the version cited in the manuscript (`v1.0.1`, DOI
`10.5281/zenodo.21427810`).

A version-specific DOI for `v1.0.2` will be added to `CITATION.cff`,
`CITATION.bib`, and this README after the new Zenodo version has been reserved
and published. Until then, cite the GitHub release URL and version number.

- Development repository: <https://github.com/enrbae/repository_graph_induced_seir_lifting>
- Previous archived release cited by the manuscript: <https://doi.org/10.5281/zenodo.21427810>

Citation metadata are provided in `CITATION.cff` and `CITATION.bib`.
The code is released under the MIT License. See `LICENSE`.
