"""Numerical configuration used in Section 5 of the article."""

from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = PROJECT_ROOT / "output"
DATA_DIR = OUTPUT_DIR / "data"
TABLES_DIR = OUTPUT_DIR / "tables"
FIGURES_DIR = OUTPUT_DIR / "figures"

# Network sizes used in the dimension and cubic-dictionary experiments.
NETWORK_SIZES = (25, 50, 100, 200, 500)

# Size used for the network-quantity and residual experiments.
DYNAMIC_NETWORK_SIZE = 100

# Sparse directed Erdos--Renyi ensemble: p = RANDOM_MEAN_DEGREE / n.
RANDOM_REALIZATIONS = 50
RANDOM_MEAN_DEGREE = 4.0
MASTER_SEED = 12345
INITIAL_SOURCE_NODE = 0
REQUIRE_INITIAL_SOURCE_OUTGOING_CHANNEL = True

# Baseline weights: every active off-diagonal channel and every diagonal
# within-subpopulation channel has unit weight.
OFF_DIAGONAL_WEIGHT = 1.0
DIAGONAL_WEIGHT = 1.0

# Dynamic weighting scenarios. The sensitivity preserves every graph support
# and rescales each receiving row to the same total incoming transmission
# intensity.
UNIT_WEIGHTING = "unit"
FIXED_INCOMING_TRANSMISSION_INTENSITY_WEIGHTING = (
    "fixed_incoming_transmission_intensity"
)
DYNAMIC_WEIGHTING_SCHEMES = (
    UNIT_WEIGHTING,
    FIXED_INCOMING_TRANSMISSION_INTENSITY_WEIGHTING,
)
FIXED_INCOMING_TRANSMISSION_INTENSITY = 1.0
WEIGHTING_LABELS = {
    UNIT_WEIGHTING: "Unit weights",
    FIXED_INCOMING_TRANSMISSION_INTENSITY_WEIGHTING: (
        "Normalized weights"
    ),
}

# SEIR parameters and dimensionless time grid.
BETA = 0.8
SIGMA = 0.25
GAMMA = 0.1
FINAL_TIME = 480.0
TIME_POINTS = 3201

# Numerical state-validation tolerances.
CONSERVATION_TOLERANCE = 1e-8
NONNEGATIVITY_TOLERANCE = 1e-8
FINAL_RESIDUAL_TOLERANCE = 1e-8
FINAL_ACTIVE_TOLERANCE = 1e-4

