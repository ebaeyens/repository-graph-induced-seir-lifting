"""First-closure residual used in the numerical illustrations."""

from __future__ import annotations

import numpy as np

from seir_network import SEIRParameters


def active_channels(adjacency: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Return arrays of receiving and source indices for all active channels."""
    receiving, source = np.nonzero(adjacency)
    return receiving.astype(int), source.astype(int)


def residual_time_series(
    trajectory: np.ndarray,
    adjacency: np.ndarray,
    parameters: SEIRParameters,
) -> np.ndarray:
    """Compute ``E_2(t) = ||r_2^E(x(t))||_2`` along a trajectory."""
    n = adjacency.shape[0]
    if trajectory.ndim != 2 or trajectory.shape[0] != 4 * n:
        raise ValueError("The trajectory has an incompatible shape.")

    receiving, source = active_channels(adjacency)
    susceptible = trajectory[0:n]
    exposed = trajectory[n : 2 * n]
    infectious = trajectory[2 * n : 3 * n]
    infection_pressure = adjacency @ infectious
    beta = parameters.beta

    r_si = (
        -beta
        * susceptible[receiving]
        * infectious[source]
        * infection_pressure[receiving]
    )
    r_se = (
        -beta
        * susceptible[receiving]
        * exposed[source]
        * infection_pressure[receiving]
        + beta
        * susceptible[receiving]
        * susceptible[source]
        * infection_pressure[source]
    )
    return np.sqrt(np.sum(r_si**2 + r_se**2, axis=0))


def residual_bound(adjacency: np.ndarray, parameters: SEIRParameters) -> float:
    """Return ``B_2 = sqrt(5m) beta delta_max^in``."""
    channels = int(np.count_nonzero(adjacency))
    maximum_weighted_in_degree = float(np.max(adjacency.sum(axis=1)))
    return float(
        np.sqrt(5.0 * channels)
        * parameters.beta
        * maximum_weighted_in_degree
    )


def time_average(times: np.ndarray, values: np.ndarray) -> float:
    """Return the trapezoidal time average on the common output grid."""
    return float(np.trapezoid(values, times) / (times[-1] - times[0]))


def first_grid_peak(times: np.ndarray, values: np.ndarray) -> tuple[float, float]:
    """Return the maximum value and its first attaining grid time."""
    index = int(np.argmax(values))
    return float(values[index]), float(times[index])
