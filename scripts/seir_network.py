"""Simulation of the networked SEIR model used in Section 5."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.integrate import solve_ivp


@dataclass(frozen=True)
class SEIRParameters:
    beta: float = 0.8
    sigma: float = 0.25
    gamma: float = 0.1


def split_state(
    state: np.ndarray,
    n: int,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Split ``x = col(S, E, I, R)`` into its four compartment vectors."""
    return (
        state[0:n],
        state[n : 2 * n],
        state[2 * n : 3 * n],
        state[3 * n : 4 * n],
    )


def localized_initial_condition(n: int, initial_fraction: float = 1e-3) -> np.ndarray:
    """Return the localized initial condition reported in the article.

    Node 1 has ``E_1(0) = I_1(0) = initial_fraction``. All other exposed,
    infectious, and removed fractions are zero.
    """
    if not 0 <= 2 * initial_fraction <= 1:
        raise ValueError("The initial exposed and infectious fractions are invalid.")

    susceptible = np.ones(n, dtype=float)
    exposed = np.zeros(n, dtype=float)
    infectious = np.zeros(n, dtype=float)
    removed = np.zeros(n, dtype=float)

    exposed[0] = initial_fraction
    infectious[0] = initial_fraction
    susceptible[0] -= 2 * initial_fraction

    return np.concatenate((susceptible, exposed, infectious, removed))


def seir_rhs(
    _time: float,
    state: np.ndarray,
    adjacency: np.ndarray,
    parameters: SEIRParameters,
) -> np.ndarray:
    """Evaluate the networked SEIR right-hand side."""
    n = adjacency.shape[0]
    susceptible, exposed, infectious, _removed = split_state(state, n)

    infection_pressure = parameters.beta * (adjacency @ infectious)
    incidence = susceptible * infection_pressure

    d_susceptible = -incidence
    d_exposed = incidence - parameters.sigma * exposed
    d_infectious = parameters.sigma * exposed - parameters.gamma * infectious
    d_removed = parameters.gamma * infectious

    return np.concatenate((d_susceptible, d_exposed, d_infectious, d_removed))


def simulate_seir(
    adjacency: np.ndarray,
    parameters: SEIRParameters,
    initial_state: np.ndarray,
    final_time: float,
    time_points: int,
):
    """Integrate the model on the common output grid used in the article."""
    times = np.linspace(0.0, final_time, time_points)
    # Integrate the original nonlinear ODE, not the approximate lifted model.
    solution = solve_ivp(
        fun=lambda time, state: seir_rhs(time, state, adjacency, parameters),
        t_span=(0.0, final_time),
        y0=initial_state,
        t_eval=times,
        method="RK45",
        rtol=1e-8,
        atol=1e-10,
    )
    if not solution.success:
        raise RuntimeError(f"SEIR integration failed: {solution.message}")
    return solution
