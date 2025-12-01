import streamlit as st
import numpy as np

from core import config
from core import signal_processing
from core import scoring
from core import plotting_utils


st.title("Step 3: Results & Interpretation")

st.markdown(
    """
    This page summarizes your hand stability test.

    We compute:
    - **Displacement** of each fingertip relative to its calibrated baseline  
    - **Tremor amplitude** (RMS of displacement)  
    - **Drift** (change from start to end)  
    - **Fatigue index** (late vs early tremor)  
    - A combined **Stability Score (0–100)**  
    """
)

st.warning(
    "Reminder: This is an educational tool and has not been clinically validated. "
    "It is **not** intended for diagnosis or medical decision-making."
)

st.divider()

# -----------------------------------
# Check prerequisites
# -----------------------------------
baseline_positions = st.session_state.get("baseline_positions", {})
raw_time_series = st.session_state.get("raw_time_series", {})
test_complete = st.session_state.get("test_complete", False)

if not baseline_positions:
    st.error("Baseline positions not found. Please complete **Step 1: Calibration** first.")
    st.stop()

if not raw_time_series or not test_complete:
    st.error("No test data found. Please complete **Step 2: Live Test** before viewing results.")
    st.stop()

# -----------------------------------
# Compute displacement and metrics
# -----------------------------------
displacement_ts = signal_processing.compute_displacement_time_series(
    raw_time_series,
    baseline_positions,
)
tremor = signal_processing.compute_tremor_metrics(displacement_ts)
drift = signal_processing.compute_drift_metrics(displacement_ts)
fatigue = signal_processing.compute_fatigue_metrics(displacement_ts)

stability_score, breakdown = scoring.compute_stability_score(
    tremor=tremor,
    drift=drift,
    fatigue=fatigue,
)

# Convenience averages (already in breakdown, but easy aliases)
avg_tremor = breakdown["avg_tremor"]
avg_drift = breakdown["avg_drift"]
avg_fatigue = breakdown["avg_fatigue"]

# -----------------------------------
# Summary metrics (cards at the top)
# -----------------------------------
st.subheader("Summary Metrics")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        "Mean Tremor (RMS)",
        f"{avg_tremor:.4f}",
        help="Average RMS of baseline-relative displacement across tracked fingers.",
    )

with col2:
    st.metric(
        "Mean Drift",
        f"{avg_drift:.4f}",
        help="Mean change in displacement from start to end of the test.",
    )

with col3:
    st.metric(
        "Mean Fatigue Index",
        f"{avg_fatigue:.2f}",
        help="Values > 1 indicate increasing tremor in the late part of the test.",
    )

with col4:
    st.metric(
        "Stability Score",
        f"{stability_score:.1f} / 100",
        help="Higher scores correspond to lower tremor, drift, and fatigue.",
    )

st.caption(
    "Note: These values are based on normalized distances in image space and are for relative comparison only."
)

st.divider()

# -----------------------------------
# Displacement over time
# -----------------------------------
st.subheader("Displacement Over Time")

st.markdown(
    """
    The plot below shows how far each fingertip moved from its baseline position
    over the duration of the test. Larger values correspond to greater movement.
    """
)

fig_disp = plotting_utils.plot_displacement_time_series(displacement_ts)
st.pyplot(fig_disp)

st.divider()

# -----------------------------------
# Fatigue analysis
# -----------------------------------
st.subheader("Fatigue by Finger")

st.markdown(
    """
    The fatigue index compares tremor amplitude in the late portion of the test
    to the early portion.

    - **≈ 1.0** → similar tremor early and late  
    - **> 1.0** → more tremor in the late portion (possible fatigue)  
    - **< 1.0** → less tremor in the late portion (possible adaptation/learning)  
    """
)

fig_fatigue = plotting_utils.plot_fatigue_bar_chart(fatigue)
st.pyplot(fig_fatigue)

st.divider()

# -----------------------------------
# Optional: Correlation between fingers
# -----------------------------------
st.subheader("Coordination Between Fingers (Optional)")

st.markdown(
    """
    Here we estimate how similarly each finger's displacement signal behaves.
    High positive correlation suggests they move together; low or negative
    correlation suggests more independent behavior.
    """
)

# Build a simple correlation matrix from displacement time series
finger_names = [f for f in config.FINGERS_TO_TRACK if displacement_ts.get(f)]
num_fingers = len(finger_names)

if num_fingers >= 2:
    # Resample displacement signals onto a common time grid for correlation
    # For simplicity, we concatenate displacement values in their original order.
    # This is a rough approximation, but sufficient for visualization here.
    signals = []

    for finger in finger_names:
        series = displacement_ts[finger]
        if not series:
            continue
        # Extract just displacement values (ignore time)
        disps = [d for _, d in series]
        signals.append(disps)

    # To handle different lengths, we truncate to the shortest signal length
    min_len = min(len(s) for s in signals)
    if min_len >= 2:
        trimmed = np.array([s[:min_len] for s in signals])
        corr_matrix = np.corrcoef(trimmed)

        fig_corr = plotting_utils.plot_correlation_heatmap(
            corr_matrix,
            finger_labels=[name.title() for name in finger_names],
        )
        st.pyplot(fig_corr)
    else:
        st.info(
            "Not enough overlapping data to compute a meaningful correlation matrix."
        )
else:
    st.info("Need at least two tracked fingers with data to compute correlation.")

st.divider()

# -----------------------------------
# Interpretation text
# -----------------------------------
st.subheader("Interpretation (Educational Only)")

st.markdown(
    f"""
    - **Tremor amplitude (~{avg_tremor:.4f})**: Higher values indicate more movement around the baseline position.
    - **Drift (~{avg_drift:.4f})**: Large positive or negative values indicate a gradual shift away from the starting posture.
    - **Fatigue index (~{avg_fatigue:.2f})**: Values above 1.0 suggest increasing tremor over time, which may be consistent with fatigue.
    - **Stability score (~{stability_score:.1f} / 100)**: Combines tremor, drift, and fatigue into a single index
      where higher values indicate more stable performance during the test.

    ⚠️ **Important:** These metrics are based on webcam tracking and simplified signal processing.
    They do not account for clinical factors and are not a substitute for professional evaluation.
    """
)
