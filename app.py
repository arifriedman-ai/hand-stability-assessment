"""Streamlit landing page for the hand stability assessment app.

This page introduces the workflow and offers a quick navigation button
into the calibration step while setting page-wide Streamlit configuration.
"""

import streamlit as st
from core import config

# -------- PAGE CONFIG --------
st.set_page_config(
    page_title="Hand Stability & Tremor Assessment",
    page_icon="🩺",
    layout="centered",
)

st.session_state["active_page"] = "home"

# -------- HEADER / TITLE --------
st.title("Hand Stability & Tremor Assessment Tool")
st.markdown(
    """
    This app estimates **multi-finger tremor, drift, and fatigue** using your webcam
    and MediaPipe hand tracking.

    It is designed as a **clinical-style assessment station** and **digital lab report**
    to explore how hand stability may change with **age, fatigue, or neurological factors**.
    """
)

# -------- QUICK OVERVIEW CARDS --------
with st.container():
    st.subheader("How it Works")
    st.markdown(
        """
        1. **Calibration** – Hold your hand steady so we can capture baseline fingertip positions.  
        2. **Live Test (≈30 sec)** – Keep your thumb, index, and middle fingers extended and steady.  
        3. **Results** – View tremor amplitude, drift, fatigue index, and a summarized stability score.
        """
    )

st.divider()

st.subheader("Get Started")

# NOTE TO AI / TEAM:
# - Optionally, implement automatic navigation to the Calibration page using Streamlit navigation helpers.
# - For now, this button can just be a visual cue, and users can click "1_Calibration" in the sidebar.

start = st.button("▶ Begin Assessment (Go to Calibration Page)", type="primary")

if start:
    try:
        # Leverage Streamlit's built-in multipage navigation to jump to Calibration.
        st.switch_page("pages/1_Calibration.py")
    except AttributeError:
        # Older Streamlit versions lack switch_page; fall back to an info message.
        st.warning(
            "Navigation helper unavailable. Please click '1_Calibration' in the sidebar to continue."
        )

st.info(
    "Use the navigation menu on the left to go to **Calibration** and start the test."
)

st.caption(
    "Disclaimer: This is an educational tool, not a medical diagnostic device."
)
