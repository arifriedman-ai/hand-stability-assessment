"""Step 1 page: collect baseline fingertip positions via MediaPipe WebRTC.

Guides the user through a short calibration recording to compute per-finger
baseline coordinates stored in Streamlit session state for later steps.
"""

import time
import uuid
from collections import defaultdict
from typing import Dict, List, Tuple

import numpy as np
import streamlit as st

from core import config
from core import mediapipe_utils


st.title("Step 1: Calibration")

st.markdown(
    """
    In this step, we capture a **baseline reference position** for your fingertips.

    **Instructions:**
    - Sit at a comfortable distance from your webcam.
    - Raise your **dominant hand** so it is fully visible.
    - Extend your **thumb, index, and middle fingers**.
    - Try to hold your hand as steady as possible inside the on-screen view.
    """
)

st.warning(
    "This tool is for educational purposes only and does **not** provide a medical diagnosis."
)

st.divider()

if "calibration_complete" not in st.session_state:
    st.session_state["calibration_complete"] = False

if "baseline_positions" not in st.session_state:
    st.session_state["baseline_positions"] = {}

CURRENT_PAGE_ID = "calibration"
previous_page = st.session_state.get("active_page")
if previous_page != CURRENT_PAGE_ID:
    st.session_state["calibration_webrtc_key"] = f"calibration-webrtc-{uuid.uuid4()}"
st.session_state["active_page"] = CURRENT_PAGE_ID
if "calibration_webrtc_key" not in st.session_state:
    st.session_state["calibration_webrtc_key"] = f"calibration-webrtc-{uuid.uuid4()}"
webrtc_stream_key = st.session_state["calibration_webrtc_key"]


# -----------------------------------
# Layout: place the WebRTC streamer and the run button side-by-side
# -----------------------------------
col_video, col_controls = st.columns([3, 1])

with col_video:
    # Initialize / reuse browser webcam stream (prompts for permission)
    webrtc_ctx = mediapipe_utils.init_webrtc_stream(webrtc_stream_key)

    # Top-aligned progress and timer placeholders (above the section title)
    progress_bar_top = st.empty()
    timer_top = st.empty()
    st.subheader("Webcam & Hand Preview")
    preview_frame_placeholder = st.empty()
    status_placeholder = st.empty()

with col_controls:
    st.subheader("Camera Controls")
    st.markdown(
        f"""
        When you are ready and your hand is steady, click the button below.
        We will record **{config.CALIBRATION_DURATION_SECONDS} seconds** of baseline fingertip data.
        """
    )
    start_calibration = st.button("▶ Run Calibration")

    if st.button("♻ Reconnect Camera"):
        st.session_state["calibration_webrtc_key"] = f"calibration-webrtc-{uuid.uuid4()}"
        if hasattr(st, "rerun"):
            st.rerun()
        else:
            st.experimental_rerun()

    st.divider()
    st.subheader("Notes & Tips")
    st.markdown(
        """
        - Ensure good lighting and keep your hand fully visible.
        - If the camera preview shows no landmarks, adjust distance or orientation.
        """
    )


# -----------------------------------
# Continuous preview before/after calibration
# -----------------------------------
fingertips, frame_rgb = mediapipe_utils.get_latest_frame_and_fingertips(webrtc_ctx)
if webrtc_ctx and webrtc_ctx.state.playing and frame_rgb is not None:
    preview_frame_placeholder.image(
        frame_rgb,
        caption="Webcam preview (with hand landmarks, if detected)",
        channels="RGB",
    )
elif not (webrtc_ctx and webrtc_ctx.state.playing):
    status_placeholder.info("Waiting for camera permission... Click 'Allow' in your browser.")
else:
    status_placeholder.info("Waiting for webcam frame... Make sure your camera is enabled.")


# -----------------------------------
# Perform calibration capture when button is clicked
# -----------------------------------
if start_calibration:
    if not (webrtc_ctx and webrtc_ctx.state.playing):
        status_placeholder.error("Camera stream is not running. Please allow camera access and try again.")
        st.stop()

    st.session_state["calibration_complete"] = False
    status_placeholder.info("Calibration in progress... Hold your hand steady.")

    # Use a dict of finger -> list of (x, y) pairs
    samples: Dict[str, List[Tuple[float, float]]] = defaultdict(list)

    start_time = time.time()
    duration = config.CALIBRATION_DURATION_SECONDS

    # Capture frames for the specified duration
    while True:
        elapsed = time.time() - start_time
        if elapsed >= duration:
            break

        fingertip_positions, frame_rgb = mediapipe_utils.get_latest_frame_and_fingertips(webrtc_ctx)

        # Update top progress bar and timer
        progress = min(1.0, elapsed / duration)
        try:
            progress_bar_top.progress(int(progress * 100))
            timer_top.markdown(f"**Calibration:** {int(duration - elapsed)}s remaining")
        except Exception:
            pass

        if frame_rgb is not None:
            preview_frame_placeholder.image(
                frame_rgb,
                caption="Calibration in progress... Keep your hand steady.",
                channels="RGB",
            )

        # If landmarks detected, store them
        if fingertip_positions:
            for finger_name, (x, y) in fingertip_positions.items():
                if finger_name in config.FINGERS_TO_TRACK:
                    samples[finger_name].append((x, y))

        # Small sleep to avoid hammering the CPU (approx 30 FPS)
        time.sleep(1 / 30.0)

    # Clear top progress/timer placeholders after capture
    try:
        progress_bar_top.empty()
        timer_top.empty()
    except Exception:
        pass

    # Compute mean position per finger
    baseline_positions: Dict[str, Tuple[float, float]] = {}

    for finger_name in config.FINGERS_TO_TRACK:
        coords = samples.get(finger_name, [])
        if len(coords) == 0:
            continue  # no data for this finger

        xs = [c[0] for c in coords]
        ys = [c[1] for c in coords]
        baseline_positions[finger_name] = (float(np.mean(xs)), float(np.mean(ys)))

    if len(baseline_positions) == 0:
        status_placeholder.error(
            "Calibration failed: no hand landmarks were detected. "
            "Please adjust your lighting and hand position, then try again."
        )
    else:
        st.session_state["baseline_positions"] = baseline_positions
        st.session_state["calibration_complete"] = True
        status_placeholder.success("Calibration complete! Baseline positions have been saved.")

        st.caption(
            "You can now move on to **Step 2: Live Test** using the navigation menu on the left."
        )
        # Automatically navigate to the Live Test page when calibration finishes
        try:
            # Attempt to stop the WebRTC stream cleanly before navigating away.
            try:
                if webrtc_ctx is not None and hasattr(webrtc_ctx, "stop"):
                    webrtc_ctx.stop()
            except Exception:
                # Best-effort stop: ignore errors to avoid crashing the app
                pass

            # small delay allows the webrtc shutdown to finish and avoids race conditions
            try:
                import time

                time.sleep(0.5)
            except Exception:
                pass

            st.switch_page("pages/2_Live_Test.py")
        except AttributeError:
            # Older Streamlit versions don't provide `switch_page`; show a friendly hint instead
            st.info("Calibration complete. Please open '2_Live_Test' from the sidebar to continue.")

# If calibration was already completed in a prior run, show a friendly reminder
if st.session_state.get("calibration_complete") and not start_calibration:
    st.success("Calibration already completed. You may proceed to the Live Test page.")
    st.caption("If needed, you can recalibrate by pressing the button again.")
