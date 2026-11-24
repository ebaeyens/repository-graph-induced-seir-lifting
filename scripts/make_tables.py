"""Create the LaTeX tables used in Section 5 from generated CSV data."""

from __future__ import annotations

import pandas as pd

from config import (
    DATA_DIR,
    FIXED_INCOMING_TRANSMISSION_INTENSITY,
    FIXED_INCOMING_TRANSMISSION_INTENSITY_WEIGHTING,
    TABLES_DIR,
    UNIT_WEIGHTING,
)


def format_number(value: float, decimals: int = 2) -> str:
    """Format an integer exactly and other numbers with fixed decimals."""
    if pd.isna(value):
        return "--"
    number = float(value)
    if abs(number - round(number)) < 1e-9:
        return f"{int(round(number)):,}"
    return f"{number:,.{decimals}f}"


def format_mean_std(mean: float, std: float, decimals: int = 2) -> str:
    """Format deterministic values or random-ensemble mean ± sample std."""
    if abs(float(std)) < 1e-12:
        return format_number(mean, decimals)
    return f"{float(mean):,.{decimals}f} $\\pm$ {float(std):,.{decimals}f}"


def write_table(
    filename: str,
    column_spec: str,
    header: str,
    rows: list[str],
    *,
    tabcolsep: int = 4,
    font_command: str = r"\small",
) -> None:
    """Write a LaTeX table fragment from formatted numerical cells."""
    lines = [
        r"\begingroup",
        font_command,
        rf"\setlength{{\tabcolsep}}{{{tabcolsep}pt}}",
        rf"\begin{{tabular}}{{{column_spec}}}",
        r"\toprule",
        header,
        r"\midrule",
        *rows,
        r"\bottomrule",
        r"\end{tabular}",
        r"\endgroup",
    ]
    (TABLES_DIR / filename).write_text("\n".join(lines) + "\n", encoding="utf-8")


def network_quantities_table() -> None:
    """Produce the manuscript table describing the three contact topologies."""
    data = pd.read_csv(DATA_DIR / "network_quantities.csv")
    rows = [
        (
            f"{row.network} & {format_number(row.n)} & "
            f"{format_mean_std(row.m, row.m_std)} & "
            f"{format_mean_std(row.Delta_in, row.Delta_in_std)} & "
            f"{format_mean_std(row.delta_max_in, row.delta_max_in_std)} \\\\"
        )
        for row in data.itertuples()
    ]
    write_table(
        "network_quantities.tex",
        "lcccc",
        r"\textbf{Network} & $\mathbf{n}$ & $\mathbf{m}$ & $\boldsymbol{\Delta}^{\mathrm{in}}$ & $\boldsymbol{\delta}_{\max}^{\mathrm{in}}$ \\",
        rows,
    )


def dimension_comparison_table() -> None:
    """Produce the graph-induced versus complete dimension table."""
    data = pd.read_csv(DATA_DIR / "dimension_comparison.csv")
    data = data[data["n"] == 100]
    rows = [
        (
            f"{row.network} & {format_number(row.n)} & "
            f"{format_number(row.D_full_2)} & "
            f"{format_mean_std(row.D_edge_2, row.D_edge_2_std)} & "
            f"{format_mean_std(row.reduction_factor, row.reduction_factor_std)} \\\\"
        )
        for row in data.itertuples()
    ]
    write_table(
        "dimension_comparison.tex",
        "lcccc",
        r"\textbf{Network} & $\mathbf{n}$ & $\mathbf{D}_{\mathrm{full},2}$ & $\mathbf{D}_{\mathrm{edge},2}$ & \textbf{Factor} \\",
        rows,
    )


def residual_summary_table() -> None:
    """Write one compact table containing both dynamic weighting cases."""
    data = pd.read_csv(DATA_DIR / "residual_sensitivity_summary.csv")
    scenario_specs = (
        (UNIT_WEIGHTING, "Unit"),
        (
            FIXED_INCOMING_TRANSMISSION_INTENSITY_WEIGHTING,
            "Normalized",
        ),
    )

    rows: list[str] = []
    for network in ("Path", "Star", "Sparse random"):
        for index, (weighting, label) in enumerate(scenario_specs):
            row = data[
                (data["network"] == network) & (data["weighting"] == weighting)
            ].iloc[0]
            network_cell = network if index == 0 else ""
            rows.append(
                f"{network_cell} & {label} & "
                f"{format_mean_std(row.E2_max, row.E2_max_std)} & "
                f"{format_mean_std(row.E2_time_average, row.E2_time_average_std, 3)} & "
                f"{format_mean_std(row.t_peak, row.t_peak_std)} & "
                f"{format_mean_std(row.B2, row.B2_std)} & "
                f"{format_mean_std(row.E2_max_over_B2, row.E2_max_over_B2_std, 4)} \\\\"
            )
        if network != "Sparse random":
            rows.append(r"\addlinespace[2pt]")

    write_table(
        "residual_summary.tex",
        "@{}llccccc@{}",
        (
            r"\textbf{Network} & \textbf{Weighting} & "
            r"$\mathbf{E}_{2,\max}$ & $\mathbf{\overline{E}}_2$ & "
            r"$\mathbf{t}_{\mathrm{peak}}$ & $\mathbf{B}_2$ & "
            r"$\mathbf{E}_{2,\max}/\mathbf{B}_2$ \\"
        ),
        rows,
        tabcolsep=2,
        font_command=r"\scriptsize",
    )


def cubic_dictionary_table() -> None:
    """Produce the cubic dictionary table for the original experiments."""
    data = pd.read_csv(DATA_DIR / "cubic_dictionary_size.csv")
    data = data[data["n"] == 100]
    rows = [
        (
            f"{row.network} & {format_number(row.n)} & "
            f"{format_number(row.D_full_3)} & "
            f"{format_mean_std(row.Phi2_dim, row.Phi2_dim_std)} & "
            f"{format_mean_std(row.Phi3_dim, row.Phi3_dim_std)} & "
            f"{format_mean_std(row.z3_edge_dim, row.z3_edge_dim_std)} \\\\"
        )
        for row in data.itertuples()
    ]
    write_table(
        "cubic_dictionary_size.tex",
        "lccccc",
        r"\textbf{Network} & $\mathbf{n}$ & $\mathbf{D}_{\mathrm{full},3}$ & $\mathbf{\dim\Phi}_2^{\mathcal{E}}$ & $\mathbf{\dim\Phi}_3^{\mathcal{E}}$ & $\mathbf{\dim z}_3^{\mathcal{E}}$ \\",
        rows,
        tabcolsep=3,
    )


def main() -> None:
    """Run this module as a command-line program and report its completed
    checks.
    """
    TABLES_DIR.mkdir(parents=True, exist_ok=True)
    network_quantities_table()
    dimension_comparison_table()
    residual_summary_table()
    cubic_dictionary_table()
    print(f"Tables written to {TABLES_DIR}")


if __name__ == "__main__":
    main()
