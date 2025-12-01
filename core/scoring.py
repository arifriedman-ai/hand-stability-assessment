"""
core/scoring.py

Combine tremor, drift, and fatigue metrics into a single 0–100 Stability Score.

Inputs:
- tremor:  dict[finger] -> tremor RMS
- drift:   dict[finger] -> drift value
- fatigue: dict[finger] -> fatigue index (late / early)

Output:
- stability_score: float (0–100, higher is more stable)
- breakdown: dict with intermediate normalized penalties and averages
"""

from __future__ import annotations

from typing import Dict, Tuple

from core import config


def _average_metric(metric: Dict[str, float]) -> float:
    """
    Compute the simple arithmetic mean of a metric across fingers.

    Returns 0.0 if the metric dict is empty.
    """
    if not metric:
        return 0.0
    values = list(metric.values())
    return float(sum(values) / len(values))


def _normalize_tremor(avg_tremor: float) -> float:
    """
    Normalize average tremor into a penalty in [0, 1].

    0 -> no tremor (best)
    1 -> at or above TREMOR_MAX_EXPECTED (worst)
    """
    max_val = max(config.TREMOR_MAX_EXPECTED, 1e-6)
    penalty = avg_tremor / max_val
    return float(max(0.0, min(1.0, penalty)))


def _normalize_drift(avg_drift: float) -> float:
    """
    Normalize average drift into a penalty in [0, 1].

    Drift can be positive or negative; we care about magnitude.
    0 -> no drift
    1 -> magnitude at or above DRIFT_MAX_EXPECTED
    """
    max_val = max(config.DRIFT_MAX_EXPECTED, 1e-6)
    penalty = abs(avg_drift) / max_val
    return float(max(0.0, min(1.0, penalty)))


def _normalize_fatigue(avg_fatigue: float) -> float:
    """
    Normalize average fatigue index into a penalty in [0, 1].

    Fatigue index:
        1.0 -> no change between early and late RMS (neutral)
        >1  -> more tremor in late portion (fatigue)
        <1  -> less tremor in late portion (could be improvement/learning)

    We treat:
        - Values <= 1.0 as zero penalty.
        - Values >= FATIGUE_MAX_EXPECTED as maximum penalty (1.0).
        - Values in between are scaled linearly.
    """
    if avg_fatigue <= 1.0:
        return 0.0

    denom = max(config.FATIGUE_MAX_EXPECTED - 1.0, 1e-6)
    penalty = (avg_fatigue - 1.0) / denom
    return float(max(0.0, min(1.0, penalty)))


def compute_stability_score(
    tremor: Dict[str, float],
    drift: Dict[str, float],
    fatigue: Dict[str, float],
) -> Tuple[float, Dict[str, float]]:
    """
    Compute a single 0–100 Stability Score from tremor, drift, and fatigue metrics.

    Parameters
    ----------
    tremor : dict
        Mapping finger name -> tremor RMS.
    drift : dict
        Mapping finger name -> drift (end - start displacement).
    fatigue : dict
        Mapping finger name -> fatigue index (late / early RMS).

    Returns
    -------
    stability_score : float
        Score in [0, 100], where:
            100 = very stable (low tremor, low drift, low fatigue)
            0   = very unstable (high tremor, high drift, high fatigue)

    breakdown : dict
        Dictionary containing intermediate averages and penalties:
            {
                "avg_tremor": ...,
                "avg_drift": ...,
                "avg_fatigue": ...,
                "penalty_tremor": ...,
                "penalty_drift": ...,
                "penalty_fatigue": ...,
                "weighted_penalty": ...,
            }
    """
    # 1) Compute simple averages across fingers
    avg_tremor = _average_metric(tremor)
    avg_drift = _average_metric(drift)
    avg_fatigue = _average_metric(fatigue)

    # 2) Normalize each into a penalty in [0, 1]
    penalty_tremor = _normalize_tremor(avg_tremor)
    penalty_drift = _normalize_drift(avg_drift)
    penalty_fatigue = _normalize_fatigue(avg_fatigue)

    # 3) Weighted combination of penalties
    w_t = config.WEIGHT_TREMOR
    w_d = config.WEIGHT_DRIFT
    w_f = config.WEIGHT_FATIGUE

    # Ensure weights sum to 1 (or rescale if they don't)
    weight_sum = w_t + w_d + w_f
    if abs(weight_sum - 1.0) > 1e-6:
        w_t /= weight_sum
        w_d /= weight_sum
        w_f /= weight_sum

    weighted_penalty = (
        w_t * penalty_tremor + w_d * penalty_drift + w_f * penalty_fatigue
    )

    # 4) Convert penalty (0=best,1=worst) to score (0=worst,100=best)
    stability_score = float(max(0.0, min(100.0, 100.0 * (1.0 - weighted_penalty))))

    breakdown = {
        "avg_tremor": avg_tremor,
        "avg_drift": avg_drift,
        "avg_fatigue": avg_fatigue,
        "penalty_tremor": penalty_tremor,
        "penalty_drift": penalty_drift,
        "penalty_fatigue": penalty_fatigue,
        "weighted_penalty": weighted_penalty,
    }

    return stability_score, breakdown
