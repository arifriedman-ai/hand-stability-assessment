"""
core/plotting_utils.py

Helper functions for creating plots of:
- Fingertip displacement over time
- Fatigue index by finger (bar chart)
- Optional correlation heatmap between finger displacement signals

All plotting functions return matplotlib Figure objects so they can be
displayed in Streamlit via st.pyplot(fig).
"""

from __future__ import annotations

from typing import Dict, List, Tuple, Sequence

import matplotlib.pyplot as plt
import numpy as np

from core import config


def plot_displacement_time_series(
    displacement_ts: Dict[str, List[Tuple[float, float]]]
):
    """
    Create a line plot of displacement vs. time for each finger.

    Parameters
    ----------
    displacement_ts : dict
        Dictionary mapping finger name -> list of (t, displacement) samples.
        Example:
        {
            "THUMB": [(t0, d0), (t1, d1), ...],
            "INDEX": [(t0, d0), (t1, d1), ...],
            "MIDDLE": [(t0, d0), (t1, d1), ...],
        }

    Returns
    -------
    matplotlib.figure.Figure
        Figure containing the displacement time series plot.
    """
    fig, ax = plt.subplots()

    for finger_name, series in displacement_ts.items():
        if not series:
            continue

        times = [t for t, _ in series]
        disps = [d for _, d in series]

        color = config.FINGER_COLORS.get(finger_name, "#000000")
        ax.plot(
            times,
            disps,
            label=finger_name.title(),
            linewidth=config.DEFAULT_LINE_WIDTH,
            color=color,
        )

    ax.set_xlabel("Time (s)")
    ax.set_ylabel("Displacement (relative to baseline, normalized units)")
    ax.set_title("Fingertip Displacement Over Time")
    ax.legend(loc="upper right")
    ax.grid(True, alpha=0.3)

    fig.tight_layout()
    return fig


def plot_fatigue_bar_chart(fatigue_metrics: Dict[str, float]):
    """
    Create a bar chart showing fatigue index per finger.

    Parameters
    ----------
    fatigue_metrics : dict
        Dictionary mapping finger name -> fatigue index (scalar).
        Example:
        {
            "THUMB": 1.2,
            "INDEX": 1.5,
            "MIDDLE": 0.9,
        }

    Returns
    -------
    matplotlib.figure.Figure
        Figure containing the fatigue bar chart.
    """
    fig, ax = plt.subplots()

    fingers = []
    values = []
    colors = []

    for finger_name in config.FINGERS_TO_TRACK:
        if finger_name not in fatigue_metrics:
            continue

        fingers.append(finger_name.title())
        values.append(fatigue_metrics[finger_name])
        colors.append(config.FINGER_COLORS.get(finger_name, "#000000"))

    if not fingers:
        # If nothing to show, just return an empty figure with a message
        ax.text(0.5, 0.5, "No fatigue data available", ha="center", va="center")
        ax.axis("off")
        fig.tight_layout()
        return fig

    x = np.arange(len(fingers))

    ax.bar(x, values, color=colors)
    ax.set_xticks(x)
    ax.set_xticklabels(fingers)
    ax.set_ylabel("Fatigue Index (late / early RMS)")
    ax.set_title("Fatigue Index by Finger")

    # Optional reference line at 1.0 (no change)
    ax.axhline(1.0, color="gray", linestyle="--", linewidth=1)
    ax.grid(axis="y", alpha=0.3)

    fig.tight_layout()
    return fig


def plot_correlation_heatmap(
    corr_matrix: Sequence[Sequence[float]],
    finger_labels: List[str],
):
    """
    Plot a simple correlation heatmap between finger displacement signals.

    Parameters
    ----------
    corr_matrix : 2D array-like
        Square matrix of shape (n_fingers, n_fingers) representing
        correlation coefficients between finger displacement signals.
    finger_labels : list of str
        Names of the fingers in the same order as corr_matrix axes.

    Returns
    -------
    matplotlib.figure.Figure
        Figure containing the correlation heatmap.
    """
    corr_array = np.asarray(corr_matrix, dtype=float)
    n = corr_array.shape[0]

    fig, ax = plt.subplots()

    cax = ax.imshow(corr_array, vmin=-1.0, vmax=1.0, cmap="coolwarm")
    fig.colorbar(cax, ax=ax, fraction=0.046, pad=0.04)

    ax.set_xticks(np.arange(n))
    ax.set_yticks(np.arange(n))
    ax.set_xticklabels(finger_labels)
    ax.set_yticklabels(finger_labels)

    # Rotate x-axis labels for readability
    plt.setp(ax.get_xticklabels(), rotation=45, ha="right", rotation_mode="anchor")

    ax.set_title("Correlation Between Finger Displacement Signals")

    # Show grid lines between cells
    ax.set_xticks(np.arange(-0.5, n, 1), minor=True)
    ax.set_yticks(np.arange(-0.5, n, 1), minor=True)
    ax.grid(which="minor", color="black", linestyle="-", linewidth=0.2)
    ax.tick_params(which="minor", bottom=False, left=False)

    fig.tight_layout()
    return fig
