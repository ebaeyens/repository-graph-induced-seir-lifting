# Reproduce each data-derived table and figure

This is the **public, item-by-item reproduction index** for the revised article
*Graph-Induced Tensor Liftings for Networked SEIR Models: Dimensional Reduction and Residual Analysis*.
It describes the numerical outputs and the programs and data distributed in this software archive.
The labels and numbers match the **currently compiled revised manuscript**.
The first numerical table is **Table 2**; the preceding Algorithm 1 is typeset
with a `longtable`, which advances LaTeX's table counter. There is no missing numerical dataset.

## 0. Start here: full reproduction and verification

From the repository root, in a clean unpacked copy, use Python **3.13.5** (see
`.python-version`) and install the exact packages in `requirements-lock.txt`
(`numpy==2.3.5`, `scipy==1.17.0`, `pandas==2.2.3`, `matplotlib==3.10.8`).
The independent test runner is `pytest==9.0.2` (`requirements-dev.txt`).

```bash
python -m venv .venv
source .venv/bin/activate  # Windows PowerShell: .venv\Scripts\Activate.ps1
python -m pip install -r requirements-lock.txt
python -m pip install -r requirements-dev.txt
python scripts/reproduce_all.py
make check
```

`reproduce_all.py` removes *only generated* `output/{data,tables,figures}` and
`experiments/{data,tables,figures,results}` and rebuilds the numerical results
without external datasets or private paths. The procedure can be time-consuming;
the program prints each stage and terminates on any failure. The item-specific
commands below are intended for re-running **after this full command**, so their
prerequisite CSVs already exist. When an item has multiple stages, the upstream
CSV is listed explicitly. All commands are run from the repository root.

The generated LaTeX table fragments are convenient intermediate files; the
journal manuscript's tables are typeset in its own `05_numerics.tex`. The
independent checker verifies **144 displayed numerical components in eight tables**
against the CSVs, with the published decimal precision:

```bash
python scripts/validate_reported_tables.py
# Optional final verification against actual journal LaTeX sources,
# available with the separate journal submission (not in this software ZIP):
python scripts/validate_reported_tables.py --manuscript /path/to/journal/LaTeX/05_numerics.tex
```

The default check uses the frozen table transcription
`experiments/reference/manuscript_table_snapshot.json`. The second check uses
actual manuscript LaTeX; do not assume that the journal sources are in this ZIP.

## 1. Table-by-table index

All input and output paths below are relative to this repository root. In the
following tables, a `;` separates multiple files. The full commands (including
required CLI arguments) are given immediately afterwards.

| Manuscript | Result | Generating program | Primary data / output |
|---|---|---|---|
| **Table 2** (`tab:network_quantities`) | Unit-weight network support | `scripts/run_experiments.py` | `output/data/network_quantities.csv` |
| **Table 3** (`tab:dimension_comparison`) | Quadratic complete ordered/symmetric versus reachable | `experiments/scripts/structural_benchmarks.py` | `experiments/data/structural_benchmarks.csv` |
| **Table 4** (`tab:residual_summary`) | First-closure residuals and simplex bounds | `experiments/scripts/graph_residual_bounds.py` | `experiments/data/refined_residual_summary.csv` |
| **Table 5** (`tab:source_sensitivity`) | Alternative initial seed nodes | `experiments/scripts/source_sensitivity.py` | `experiments/data/source_node_sensitivity.csv` |
| **Table 6** (`tab:cubic_dictionary_size`) | Cumulative cubic lifting dimensions | `scripts/run_experiments.py` | `output/data/cubic_dictionary_size.csv` |
| **Table 7** (`tab:carleman_costs`) | Matched small-network Carleman costs | `experiments/scripts/carleman_cost_comparison.py` | `experiments/data/carleman_costs.csv` |
| **Table 8** (`tab:workplace_contacts`) | SocioPatterns workplace contact support | `experiments/scripts/sociopatterns_workplace.py` | `experiments/data/workplace_topology.csv` |
| **Table 9** (`tab:truncation_accuracy`) | Finite-horizon lifted trajectory error by order | `experiments/scripts/truncation_accuracy.py` | `experiments/data/truncation_accuracy.csv` |

### Exact table commands and prerequisites

The following commands reproduce the **generating data** for each table.
For tables whose entry point depends on earlier stages, first run the full
workflow above or regenerate its stated inputs.

**Table 2 — Unit-weight network support.**

```bash
python scripts/run_experiments.py --stage structural
```

Inputs: `scripts/run_experiments.py`, `scripts/config.py`.

Outputs: `output/data/network_quantities.csv`, `output/tables/network_quantities.tex`.

The table is typeset in the journal source; the CSV records the three support types at n=100.

**Table 3 — Quadratic complete ordered/symmetric versus reachable.**

```bash
python experiments/scripts/structural_benchmarks.py --repo . --out experiments/data/structural_benchmarks.csv
```

Inputs: `output/data/network_quantities.csv`, `output/data/dimension_comparison.csv`, `output/data/cubic_dictionary_size.csv`, `experiments/scripts/structural_benchmarks.py`.

Outputs: `experiments/data/structural_benchmarks.csv`, `output/data/dimension_comparison.csv`, `experiments/tables/symmetric_benchmarks.tex`.

Generate the original structural CSVs first. The current journal values are checked by the table validator.

**Table 4 — First-closure residuals and simplex bounds.**

```bash
python experiments/scripts/graph_residual_bounds.py --repo . --out experiments/data/refined_residual_summary.csv --rawout experiments/data/refined_bounds_by_realization.csv
```

Inputs: `output/data/residual_sensitivity_summary.csv`, `output/data/sparse_random_residual_realizations.csv`, `experiments/scripts/graph_residual_bounds.py`.

Outputs: `experiments/data/refined_residual_summary.csv`, `experiments/data/refined_bounds_by_realization.csv`, `experiments/tables/refined_residuals.tex`.

Requires completion of the original dynamic simulation stage.

**Table 5 — Alternative initial seed nodes.**

```bash
python experiments/scripts/source_sensitivity.py --repo . --out experiments/data/source_node_sensitivity.csv --randomout experiments/data/random_normalized_rms.csv
```

Inputs: `output/data/residual_sensitivity_summary.csv`, `output/data/sparse_random_residual_realizations.csv`, `experiments/scripts/source_sensitivity.py`.

Outputs: `experiments/data/source_node_sensitivity.csv`, `experiments/data/random_normalized_rms.csv`, `experiments/tables/initial_node_sensitivity.tex`.

Uses the specified alternative infection locations with the same SEIR parameters.

**Table 6 — Cumulative cubic lifting dimensions.**

```bash
python scripts/run_experiments.py --stage structural
```

Inputs: `scripts/run_experiments.py`, `scripts/lifting_metrics.py`.

Outputs: `output/data/cubic_dictionary_size.csv`, `output/tables/cubic_dictionary_size.tex`, `experiments/data/structural_benchmarks.csv`.

For the complete symmetric/ordered columns also run structural_benchmarks.py after generating the original structural outputs.

**Table 7 — Matched small-network Carleman costs.**

```bash
python experiments/scripts/carleman_cost_comparison.py --repo . --out experiments/data/carleman_costs.csv --repeats 5
```

Inputs: `experiments/scripts/carleman_cost_comparison.py`, `experiments/scripts/carleman_operators.py`, `experiments/reference/carleman_costs_reference.csv`.

Outputs: `experiments/data/carleman_costs.csv`.

Coordinates and CSR size are reproducible; printed times use archived five-run medians from carleman_costs_reference.csv, and a new computer need not reproduce the same seconds.

**Table 8 — SocioPatterns workplace contact support.**

```bash
python experiments/scripts/sociopatterns_workplace.py --repo . --out experiments/data --repeats 30
```

Inputs: `experiments/scripts/sociopatterns_workplace.py`, `experiments/source_data/workplace_InVS_tij.dat.zip`, `experiments/source_data/PROVENANCE.md`.

Outputs: `experiments/data/workplace_topology.csv`, `experiments/data/workplace_residuals.csv`, `experiments/data/workplace_daily_contacts.csv`, `experiments/data/workplace_summary.json`.

Observed contacts are aggregated to a fixed support; 92 assumed within-node model channels are not measured contacts. Seeds of the 30 matched synthetic graphs are recorded in workplace_topology.csv.

**Table 9 — Finite-horizon lifted trajectory error by order.**

```bash
python experiments/scripts/truncation_accuracy.py --repo . --out experiments/data/truncation_accuracy.csv
```

Inputs: `experiments/scripts/truncation_accuracy.py`.

Outputs: `experiments/data/truncation_accuracy.csv`.

Three-node path/star, truncation orders 2 to 5; finite-horizon diagnostic, not a convergence test.

## 2. Data-derived figure index

Figure 1 is an author-drawn TikZ illustration in the journal manuscript, not a
numerical result; it is therefore outside the scope of this software archive
and its reproducibility checks.

**Figure 2 — Ordered, symmetric and reachable dimensions** (`fig:dimension_comparison`).

Entry point: `python experiments/scripts/make_dimension_figure.py --source experiments/data/structural_benchmarks.csv --out experiments/figures/figure_2_dimension_comparison.pdf`.

Inputs: `experiments/data/structural_benchmarks.csv`, `experiments/scripts/make_dimension_figure.py`.

Output: `experiments/figures/figure_2_dimension_comparison.pdf`.

Regenerate the structural benchmarks before this command. The journal submission stores a copy under figures/.

**Figure 3 — Unit-weight residual curves** (`fig:residual_dynamics_unit`).

Entry point: `python scripts/make_figures.py`.

Inputs: `output/data/residual_sensitivity_timeseries.csv`, `scripts/make_figures.py`.

Output: `output/figures/residual_dynamics_unit.pdf`.

Requires original dynamic outputs; the journal submission includes this plot as figure_3_unit_weights_residuals.pdf.

**Figure 4 — Normalized-weight residual curves** (`fig:residual_dynamics_fixed`).

Entry point: `python scripts/make_figures.py`.

Inputs: `output/data/residual_sensitivity_timeseries.csv`, `scripts/make_figures.py`.

Output: `output/figures/residual_dynamics_fixed_incoming_transmission_intensity.pdf`.

Requires original dynamic outputs; journal-source copy is figure_4_fixed_incoming_transmission_intensity.pdf.

**Figure 5 — Cubic dictionary dimension by topology** (`fig:higher_order_dictionary_size`).

Entry point: `python scripts/make_figures.py`.

Inputs: `output/data/cubic_dictionary_size.csv`, `scripts/make_figures.py`.

Output: `output/figures/higher_order_dictionary_size.pdf`.

Requires original structural outputs; journal-source copy is figure_5_higher_order_dictionary_size.pdf.

## 3. Random-number generator and admitted realizations

- Generator: `numpy.random.default_rng`, **PCG64** in the pinned NumPy
  environment; master seed **12345**, separate size-dependent stream initialized
  as `12345+n` for `n=25, 50, 100, 200, 500`.
- For each size the script accepts 50 randomly drawn **directed** sparse-graph
  realizations only if the initially infected node has at least one off-diagonal
  **outgoing transmission channel**. The 250 accepted realization IDs and
  **actual integer seeds** are archived, without relying on just the master seed,
  in `output/data/sparse_random_realizations.csv` (`n,realization,seed,...`).
- Residual and trajectory calculations use the same accepted supports for unit
  and normalized weights. The source-level cross-reference is
  `output/data/sparse_random_residual_realizations.csv`.
- The SocioPatterns benchmark has **30** matched undirected `G(92,755)` networks,
  generated with integer seeds **20261112 through 20261141**. The actual seeds
  and structural results are recorded in `experiments/data/workplace_topology.csv`,
  and the full seed list is also in `experiments/data/workplace_summary.json`.
- Other deterministic/scoped random streams are declared in their relevant
  generator scripts (`experiments/scripts/`). Do not substitute a single master
  seed for scripts that establish their own fixed cases.

## 4. Source data, numerical environment, limitations

The original temporal proximity source is included at
`experiments/source_data/workplace_InVS_tij.dat.zip`; see
`experiments/source_data/PROVENANCE.md` for provenance, license and checksum.
Every model node's diagonal transmission channel is an **assumption**, not
an observed self-contact; the contact sequence is aggregated to a static
support and is not a calibrated epidemiological observation of infection.

Dynamics: `scipy.integrate.solve_ivp` with **RK45**, relative tolerance
`1e-8`, absolute tolerance `1e-10`, and the reference time grid of 3,201
points over `[0,480]` for the main simulations. Different scripts intentionally
use their explicitly documented horizons (e.g., 60 for the workplace example,
12 for the small-network trajectory-error experiment).

Monomial dimensions, channel counts, CSR array bytes and accepted seeds are
structural outputs. Floating-point summaries are checked within stated
precision. **Recorded wall times, traced Python allocations and process memory
are hardware- and runtime-dependent**: the values printed in Table 7 use
`experiments/reference/carleman_costs_reference.csv` as an archived measured
baseline. A new execution of `carleman_cost_comparison.py` is expected to match
basis dimensions and CSR bytes, but not necessarily the seconds.

Run `python scripts/check_reproducibility_index.py` to check that this index's
machine-readable companion `doc/reproducibility_map.json` covers all eight
numerical tables and four data-derived figures (Figures 2–5), and that all
internal source/result paths exist in the release.
