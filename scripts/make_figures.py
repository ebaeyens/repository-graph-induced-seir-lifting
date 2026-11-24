"""Create the three PDF figures used in Section 5 from generated CSV data."""

from __future__ import annotations

import matplotlib.pyplot as plt
from matplotlib.ticker import NullFormatter
from mpl_toolkits.axes_grid1.inset_locator import inset_axes
import pandas as pd

from config import (
    DATA_DIR,
    FIGURES_DIR,
    FINAL_TIME,
    FIXED_INCOMING_TRANSMISSION_INTENSITY_WEIGHTING,
    UNIT_WEIGHTING,
)


NETWORK_SIZES = [25, 50, 100, 200, 500]
NETWORK_STYLE = {
    "Path": {"color": "#1f77b4", "marker": "o", "linestyle": "-"},
    "Star": {"color": "#2ca02c", "marker": "s", "linestyle": "--"},
    "Sparse random": {"color": "#d62728", "marker": "^", "linestyle": "-."},
}


def configure_matplotlib() -> None:
    """Use a compact serif style compatible with the manuscript."""
    plt.rcParams.update(
        {
            "font.family": "serif",
            "font.serif": ["Computer Modern Roman", "CMU Serif", "DejaVu Serif"],
            "mathtext.fontset": "cm",
            "axes.labelsize": 10,
            "xtick.labelsize": 9,
            "ytick.labelsize": 9,
            "legend.fontsize": 8.5,
            "axes.linewidth": 0.7,
            "lines.linewidth": 1.7,
            "lines.markersize": 4.5,
            "pdf.fonttype": 42,
        }
    )


def new_figure():
    """Start a figure with the publication plotting defaults."""
    return plt.subplots(figsize=(5.2, 3.2), constrained_layout=True)


def finish_axes(axis, *, logarithmic: bool = False, legend: bool = True) -> None:
    """Apply axis labeling, grids and legends consistently across plots."""
    if logarithmic:
        axis.set_xscale("log")
        axis.set_yscale("log")
        axis.set_xticks(NETWORK_SIZES)
        axis.set_xticklabels([str(n) for n in NETWORK_SIZES])
        axis.xaxis.set_minor_formatter(NullFormatter())
    axis.grid(True, which="major", linewidth=0.45, alpha=0.65)
    axis.grid(True, which="minor", linewidth=0.3, alpha=0.35, linestyle=":")
    if legend:
        axis.legend(frameon=True, fancybox=False, framealpha=0.95)


def plot_network_curve(axis, data: pd.DataFrame, column: str, network: str) -> None:
    """Add one network-dependent curve to the selected axis."""
    subset = data[data["network"] == network].sort_values("n")
    style = NETWORK_STYLE[network]
    axis.plot(
        subset["n"],
        subset[column],
        label=network,
        markerfacecolor="white",
        markeredgewidth=1.0,
        **style,
    )


def dimension_comparison_figure() -> None:
    """Generate the quadratic-dimension comparison in Figure 2."""
    data = pd.read_csv(DATA_DIR / "dimension_comparison.csv")
    path = data[data["network"] == "Path"].sort_values("n")
    random = data[data["network"] == "Sparse random"].sort_values("n")

    figure, axis = new_figure()
    axis.plot(
        path["n"],
        path["D_edge_2"],
        label="Path/Star: edge",
        color="#1f77b4",
        marker="o",
        linestyle="-",
        markerfacecolor="white",
    )
    axis.plot(
        random["n"],
        random["D_edge_2"],
        label="Sparse random: edge",
        color="#2ca02c",
        marker="s",
        linestyle="--",
        markerfacecolor="white",
    )
    axis.plot(
        path["n"],
        path["D_full_2"],
        label="Complete ordered: quadratic",
        color="#d62728",
        marker="D",
        linestyle=":",
        markerfacecolor="white",
    )
    axis.set_xlabel("Number of nodes")
    axis.set_ylabel("Dimension")
    finish_axes(axis, logarithmic=True)
    figure.savefig(FIGURES_DIR / "dimension_comparison.pdf")
    plt.close(figure)


def _plot_residual_series(axis, subset_weighting: pd.DataFrame) -> None:
    """Plot the original trajectory residuals and uncertainty bands."""
    for network in ("Path", "Star", "Sparse random"):
        subset = subset_weighting[
            subset_weighting["network"] == network
        ].sort_values("t")
        style = NETWORK_STYLE[network]
        axis.plot(
            subset["t"],
            subset["E2"],
            label=network,
            markevery=max(len(subset) // 12, 1),
            markerfacecolor="white",
            markeredgewidth=1.0,
            **style,
        )
        if network == "Sparse random":
            lower = (subset["E2"] - subset["E2_std"]).clip(lower=0.0)
            upper = subset["E2"] + subset["E2_std"]
            axis.fill_between(
                subset["t"],
                lower,
                upper,
                color=style["color"],
                alpha=0.16,
                linewidth=0,
            )


def residual_dynamics_unit_figure() -> None:
    """Generate the unit-weight residual panel with an early-time inset."""
    data = pd.read_csv(DATA_DIR / "residual_sensitivity_timeseries.csv")
    subset_weighting = data[data["weighting"] == UNIT_WEIGHTING]

    figure, axis = new_figure()
    _plot_residual_series(axis, subset_weighting)
    axis.set_xlabel("Time (simulation units)")
    axis.set_ylabel(r"$E_2(t)$")
    axis.set_xlim(0, 240)
    axis.set_xticks([0, 60, 120, 180, 240])
    finish_axes(axis, legend=False)
    axis.legend(loc="upper right", frameon=True, fancybox=False, framealpha=0.95)

    inset = inset_axes(axis, width="44%", height="44%", loc="center right", borderpad=1.1)
    _plot_residual_series(inset, subset_weighting)
    inset.set_xlim(0, 20)
    inset.set_xticks([0, 10, 20])
    inset.grid(True, which="major", linewidth=0.35, alpha=0.55)
    inset.grid(True, which="minor", linewidth=0.25, alpha=0.30, linestyle=":")
    inset.tick_params(labelsize=7)
    inset.set_ylabel("")
    inset.set_xlabel("")

    figure.savefig(FIGURES_DIR / "residual_dynamics_unit.pdf")
    plt.close(figure)


def residual_dynamics_fixed_intensity_figure() -> None:
    """Generate the fixed-incoming-transmission-intensity residual panel."""
    data = pd.read_csv(DATA_DIR / "residual_sensitivity_timeseries.csv")
    subset_weighting = data[
        data["weighting"] == FIXED_INCOMING_TRANSMISSION_INTENSITY_WEIGHTING
    ]

    figure, axis = new_figure()
    _plot_residual_series(axis, subset_weighting)
    axis.set_xlabel("Time (simulation units)")
    axis.set_ylabel(r"$E_2(t)$")
    axis.set_xlim(0, FINAL_TIME)
    axis.set_xticks([0, 120, 240, 360, 480])
    finish_axes(axis, legend=False)
    axis.legend(loc="upper right", frameon=True, fancybox=False, framealpha=0.95)

    inset = inset_axes(axis, width="44%", height="44%", loc="center right", borderpad=1.1)
    _plot_residual_series(inset, subset_weighting)
    inset.set_xlim(0, 60)
    inset.set_xticks([0, 30, 60])
    inset.grid(True, which="major", linewidth=0.35, alpha=0.55)
    inset.grid(True, which="minor", linewidth=0.25, alpha=0.30, linestyle=":")
    inset.tick_params(labelsize=7)
    inset.set_ylabel("")
    inset.set_xlabel("")

    figure.savefig(FIGURES_DIR / "residual_dynamics_fixed_incoming_transmission_intensity.pdf")
    plt.close(figure)


def cubic_dictionary_figure() -> None:

    """Generate the linearly closed cubic-dictionary sizes in Figure 5."""
    data = pd.read_csv(DATA_DIR / "cubic_dictionary_size.csv")
    figure, axis = new_figure()

    for network in ("Path", "Star", "Sparse random"):
        plot_network_curve(axis, data, "Phi3_dim", network)

    axis.set_xlabel("Number of nodes")
    axis.set_ylabel(r"$\dim \Phi_3^{\mathcal{E}}$")
    finish_axes(axis, logarithmic=True)
    figure.savefig(FIGURES_DIR / "higher_order_dictionary_size.pdf")
    plt.close(figure)


def main() -> None:
    """Run this module as a command-line program and report its completed
    checks.
    """
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    configure_matplotlib()
    dimension_comparison_figure()
    residual_dynamics_unit_figure()
    residual_dynamics_fixed_intensity_figure()
    cubic_dictionary_figure()
    print(f"Figures written to {FIGURES_DIR}")


if __name__ == "__main__":
    main()
