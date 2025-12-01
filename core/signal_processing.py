"""
core/signal_processing.py

Functions for converting raw fingertip trajectories into:
- Displacement time series relative to baseline
- Tremor metrics (RMS amplitude)
- Drift metrics (change in displacement over the test)
- Fatigue metrics (late vs early tremor amplitude)

The inputs are:
- raw_data: dict[finger] -> list of (t, x, y)
- baseline_positions: dict[finger] -> (x0, y0)

All times t are assumed to be in seconds relative to test start.
All coordinates x, y are assumed to be normalized in [0, 1].
"""

from __future__ import annotations

from typing import Dict, List, Tuple

import math
import numpy as np

from core import config


# Type aliases for clarity
RawTimeSeries = Dict[str, List[Tuple[float, float, float]]]
BaselinePositions = Dict[str, Tuple[float, float]]
DisplacementTimeSeries = Dict[str, List[Tuple[float, float]]]


def compute_displacement_time_series(
    raw_data: RawTimeSeries,
    baseline_positions: BaselinePositions,
) -> DisplacementTimeSeries:
    """
    Convert raw fingertip trajectories into displacement time series.

    Parameters
    ----------
    raw_data : dict
        Mapping finger name -> list of (t, x, y) samples.
        Example:
            {
                "THUMB": [(t0, x0, y0), (t1, x1, y1), ...],
                "INDEX": [...],
                "MIDDLE": [...],
            }

    baseline_positions : dict
        Mapping finger name -> (x0, y0) baseline coordinates (from calibration).
        Example:
            {
                "THUMB": (x0_thumb, y0_thumb),
                "INDEX": (x0_index, y0_index),
                "MIDDLE": (x0_middle, y0_middle),
            }

    Returns
    -------
    dict
        Mapping finger name -> list of (t, displacement) samples, where
        displacement is the Euclidean distance from the baseline position,
        in normalized coordinate units.
    """
    displacement_ts: DisplacementTimeSeries = {}

    for finger_name in config.FINGERS_TO_TRACK:
        samples = raw_data.get(finger_name, [])
        baseline = baseline_positions.get(finger_name, None)

        if not samples or baseline is None:
            displacement_ts[finger_name] = []
            continue

        x0, y0 = baseline
        series: List[Tuple[float, float]] = []

        for (t, x, y) in samples:
            dx = x - x0
            dy = y - y0
            disp = math.sqrt(dx * dx + dy * dy)
            series.append((float(t), float(disp)))

        displacement_ts[finger_name] = series

    return displacement_ts


def _rms(values: List[float]) -> float:
    """
    Compute the root mean square (RMS) of a list of values.
    Returns 0.0 if the list is empty.
    """
    if not values:
        return 0.0
    arr = np.asarray(values, dtype=float)
    return float(math.sqrt(np.mean(arr * arr)))


def compute_tremor_metrics(
    displacement_ts: DisplacementTimeSeries,
) -> Dict[str, float]:
    """
    Compute overall tremor amplitude (RMS displacement) for each finger.

    Parameters
    ----------
    displacement_ts : dict
        Mapping finger name -> list of (t, displacement) samples.

    Returns
    -------
    dict
        Mapping finger name -> tremor RMS (scalar).
    """
    tremor: Dict[str, float] = {}

    for finger_name, series in displacement_ts.items():
        displacements = [d for _, d in series]
        tremor[finger_name] = _rms(displacements)

    return tremor


def compute_drift_metrics(
    displacement_ts: DisplacementTimeSeries,
) -> Dict[str, float]:
    """
    Compute drift for each finger as:
        drift = displacement_end - displacement_start

    Parameters
    ----------
    displacement_ts : dict
        Mapping finger name -> list of (t, displacement) samples.

    Returns
    -------
    dict
        Mapping finger name -> drift (scalar). Positive values indicate
        an increase in displacement from baseline over the test.
    """
    drift: Dict[str, float] = {}

    for finger_name, series in displacement_ts.items():
        if len(series) < 2:
            drift[finger_name] = 0.0
            continue

        # Series is list of (t, d); assume chronological order
        d_start = series[0][1]
        d_end = series[-1][1]
        drift[finger_name] = float(d_end - d_start)

    return drift


def compute_fatigue_metrics(
    displacement_ts: DisplacementTimeSeries,
) -> Dict[str, float]:
    """
    Compute fatigue index for each finger.

    Fatigue index is defined as:
        fatigue = RMS_late / RMS_early

    where:
    - RMS_early is computed over samples in the early portion of the test.
    - RMS_late is computed over samples in the late portion of the test.

    We attempt to use a 10-second early and 10-second late window if possible,
    based on the times present in the series. If the full test duration is
    shorter than 20 seconds, we fall back to splitting by time fraction:
    early = first half, late = second half.

    Parameters
    ----------
    displacement_ts : dict
        Mapping finger name -> list of (t, displacement) samples.

    Returns
    -------
    dict
        Mapping finger name -> fatigue index (scalar).
        Values > 1 indicate increasing tremor over the test.
        If not enough data is available, returns 1.0 for that finger.
    """
    fatigue: Dict[str, float] = {}

    for finger_name, series in displacement_ts.items():
        if len(series) < 2:
            fatigue[finger_name] = 1.0
            continue

        times = [t for t, _ in series]
        displacements = [d for _, d in series]

        t_min = float(min(times))
        t_max = float(max(times))
        total_span = t_max - t_min

        # Choose early / late windows
        early_mask = []
        late_mask = []

        if total_span >= 20.0:
            # Use fixed 10 s windows when enough data available
            early_end = t_min + 10.0
            late_start = t_max - 10.0

            for t in times:
                if t <= early_end:
                    early_mask.append(True)
                    late_mask.append(False)
                elif t >= late_start:
                    early_mask.append(False)
                    late_mask.append(True)
                else:
                    early_mask.append(False)
                    late_mask.append(False)
        else:
            # Fallback: split by halves
            mid = t_min + total_span / 2.0
            for t in times:
                if t <= mid:
                    early_mask.append(True)
                    late_mask.append(False)
                else:
                    early_mask.append(False)
                    late_mask.append(True)

        # Extract early & late displacement values
        early_values = [d for d, m in zip(displacements, early_mask) if m]
        late_values = [d for d, m in zip(displacements, late_mask) if m]

        # If one of the segments is empty, fall back to neutral fatigue = 1.0
        if not early_values or not late_values:
            fatigue[finger_name] = 1.0
            continue

        early_rms = _rms(early_values)
        late_rms = _rms(late_values)

        # Avoid division by very small numbers
        if early_rms < 1e-6:
            fatigue_index = 1.0
        else:
            fatigue_index = float(late_rms / early_rms)

        fatigue[finger_name] = fatigue_index

    return fatigue
