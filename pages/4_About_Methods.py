import streamlit as st

st.session_state["active_page"] = "about"

st.title("About This Project & Methods")

st.markdown(
    """
### 📌 Purpose of the Tool
This project explores how **hand tremor, drift, and fatigue** can be quantified using
computer vision. Our goal is to simulate a **clinical-style motor steadiness test** and
display metrics that reflect movement stability over time.

This is an **educational biomechanics + signal processing project**, NOT a diagnostic tool.

---

### 🔷 How the System Works (Pipeline)

1. **Calibration**
   - The user holds their hand still for ~3 seconds.
   - The app estimates a baseline fingertip position for:
     - Thumb
     - Index finger
     - Middle finger

2. **Live Test (~30 seconds)**
   - MediaPipe + OpenCV track fingertip positions over time.
   - Raw 2D coordinates are recorded at ~30 FPS.

3. **Signal Processing**
   We convert fingertip movement into displacement relative to baseline:

   \[
   d(t) = \sqrt{(x(t)-x_0)^2 + (y(t)-y_0)^2}
   \]

   From this, we compute three key features:

   | Metric | Meaning | Interpretation |
   |--------|---------|----------------|
   | **Tremor (RMS)** | Variation in baseline displacement | Higher = less steady |
   | **Drift** | Change in position from start→end | Higher = gradual loss of posture |
   | **Fatigue Index** | Late tremor / Early tremor | >1.0 may indicate muscular fatigue |

4. **Stability Score (0–100)**
   A weighted score combines all metrics:

   \[
   Score = 100 \times (1 - (w_T T + w_D D + w_F F))
   \]

   Higher = steadier performance.

---

### 🔬 Why MediaPipe?
MediaPipe Hands is a fast, lightweight ML-based model that detects 21 hand landmarks
in real-time without specialized hardware. It enables in-browser motor tracking
without sensors, EMG, or gloves.

---

### ⚠ Ethical & Clinical Disclaimer

This application:

- ❗ is not FDA-approved  
- ❗ should not be used for medical assessment  
- ❗ is meant for research, education, & exploratory biomechanics only  

Any conclusions must be interpreted cautiously.

---

### 👨‍💻 Project Credit
Developed using:

| Library | Purpose |
|--------|----------|
| Streamlit | UI + multipage app |
| MediaPipe | Hand tracking & landmark detection |
| OpenCV | Webcam capture |
| NumPy | Signal processing |
| Matplotlib | Visualization |

---

If you'd like, scroll back through the pages and **re-run the test** to compare results over time!
"""
)
