"""
core/config.py

Central configuration module for the Hand Stability & Tremor Assessment Tool.

This file stores:
- Test durations
- Which fingers we track
- Color mappings for each finger
- Weights used when computing the overall Stability Score

All other modules should import from here instead of hard-coding values.
"""

# -----------------------------
# TIMING PARAMETERS (seconds)
# -----------------------------

#: Duration of the calibration phase (seconds)
CALIBRATION_DURATION_SECONDS: int = 3

#: Duration of the live test phase (seconds)
TEST_DURATION_SECONDS: int = 30


# -----------------------------
# FINGERS WE TRACK
# -----------------------------
# We focus on three fingertips: thumb, index, middle.

#: List of finger names used throughout the app
FINGERS_TO_TRACK = ["THUMB", "INDEX", "MIDDLE"]


# -----------------------------
# COLOR MAPPINGS
# -----------------------------
# Hex color codes used for plotting and UI consistency.
# These align with the teal + neutral gray clinical theme.

FINGER_COLORS = {
    "THUMB": "#1E88E5",   # Blue
    "INDEX": "#43A047",   # Green
    "MIDDLE": "#E53935",  # Red
}

#: Default line width for plots (can be used by plotting_utils)
DEFAULT_LINE_WIDTH: float = 2.0


# -----------------------------
# STABILITY SCORE WEIGHTS
# -----------------------------
# These weights determine how much each component contributes
# to the final 0–100 Stability Score.

#: Weight for tremor amplitude component (0–1, will be normalized)
WEIGHT_TREMOR: float = 0.4

#: Weight for drift component (0–1, will be normalized)
WEIGHT_DRIFT: float = 0.3

#: Weight for fatigue component (0–1, will be normalized)
WEIGHT_FATIGUE: float = 0.3


# -----------------------------
# NORMALIZATION CONSTANTS
# -----------------------------
# These are rough upper bounds used to normalize metrics into [0, 1].
# You can tweak these if initial results look too compressed or saturated.

#: Approximate maximum tremor amplitude we expect (in arbitrary displacement units)
TREMOR_MAX_EXPECTED: float = 0.05

#: Approximate maximum drift we expect (in displacement units)
DRIFT_MAX_EXPECTED: float = 0.1

#: Reasonable upper bound for fatigue index (late/early).
#: Values much larger than this will be clipped.
FATIGUE_MAX_EXPECTED: float = 2.0


# -----------------------------
# UTILITY FLAGS / OPTIONS
# -----------------------------

#: If True, extra debug info can be printed/logged by other modules
DEBUG_MODE: bool = False
