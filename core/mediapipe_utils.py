"""
core/mediapipe_utils.py

Helper functions for working with MediaPipe Hands and a webcam.

Responsibilities:
- Initialize a MediaPipe Hands context.
- Open and manage a webcam video capture stream.
- Read frames from the webcam.
- Detect hand landmarks.
- Extract fingertip coordinates for the THUMB, INDEX, and MIDDLE fingers.

All coordinates returned are normalized (0–1) in image space:
- x: 0 = left, 1 = right
- y: 0 = top, 1 = bottom
"""

from __future__ import annotations

from typing import Dict, Optional, Tuple

import cv2
import mediapipe as mp

from core import config


# MediaPipe setup (shared across functions)
mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils
mp_drawing_styles = mp.solutions.drawing_styles


# Mapping from our finger names to MediaPipe landmark indices for fingertips.
# See: https://developers.google.com/mediapipe/solutions/vision/hand_landmarker
FINGERTIP_INDICES = {
    "THUMB": 4,
    "INDEX": 8,
    "MIDDLE": 12,
}


class MediaPipeContext:
    """
    Small wrapper class to hold MediaPipe Hands and webcam VideoCapture.

    This makes it easier to pass a single object around during calibration
    and the live test, and to cleanly release resources when done.
    """

    def __init__(self, camera_index: int = 0):
        # Initialize MediaPipe Hands
        self.hands = mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=1,  # we only care about one hand at a time
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5,
        )

        # Initialize webcam
        self.cap = cv2.VideoCapture(camera_index)

    def release(self) -> None:
        """Release the MediaPipe and webcam resources."""
        if self.hands is not None:
            self.hands.close()
        if self.cap is not None and self.cap.isOpened():
            self.cap.release()


def init_mediapipe_hands(camera_index: int = 0) -> MediaPipeContext:
    """
    Create and return a MediaPipeContext with a Hands object and webcam.

    Parameters
    ----------
    camera_index : int
        Index of the webcam to use (0 by default).

    Returns
    -------
    MediaPipeContext
        Context containing MediaPipe Hands and an open VideoCapture.
    """
    return MediaPipeContext(camera_index=camera_index)


def _extract_fingertip_coords(landmarks, image_width: int, image_height: int) -> Dict[str, Tuple[float, float]]:
    """
    Internal helper to extract normalized fingertip coordinates from a list
    of landmarks for the fingers defined in config.FINGERS_TO_TRACK.

    Parameters
    ----------
    landmarks :
        List of 21 hand landmarks from MediaPipe.
    image_width : int
        Width of the image in pixels.
    image_height : int
        Height of the image in pixels.

    Returns
    -------
    dict
        Mapping finger name -> (x_norm, y_norm), both in [0, 1].
    """
    fingertip_positions: Dict[str, Tuple[float, float]] = {}

    for finger_name in config.FINGERS_TO_TRACK:
        mp_index = FINGERTIP_INDICES.get(finger_name)
        if mp_index is None:
            continue

        lm = landmarks[mp_index]

        # MediaPipe landmarks are already normalized (x, y in [0, 1])
        x_norm = float(lm.x)
        y_norm = float(lm.y)

        # Clamp to [0, 1] just to be safe
        x_norm = max(0.0, min(1.0, x_norm))
        y_norm = max(0.0, min(1.0, y_norm))

        fingertip_positions[finger_name] = (x_norm, y_norm)

    return fingertip_positions


def capture_frame_and_landmarks(
    context: MediaPipeContext,
    draw_landmarks: bool = True,
) -> Tuple[Optional[Dict[str, Tuple[float, float]]], Optional[any]]:
    """
    Capture a single frame from the webcam, run MediaPipe Hand detection,
    and return the fingertip coordinates + an annotated image.

    Parameters
    ----------
    context : MediaPipeContext
        The MediaPipe context containing Hands and VideoCapture.
    draw_landmarks : bool
        If True, hand landmarks and connections are drawn on the frame.

    Returns
    -------
    fingertip_positions : dict or None
        Mapping finger name -> (x_norm, y_norm) for THUMB, INDEX, MIDDLE.
        Returns None if no hand is detected or capture fails.
    frame_rgb : numpy.ndarray or None
        The RGB image (annotated if draw_landmarks=True) suitable for display
        in Streamlit via st.image(). Returns None if capture fails.

    Notes
    -----
    - This function does NOT loop; it captures only a single frame.
      The caller (e.g., a page in Streamlit) should call it repeatedly
      inside a time-controlled loop for calibration or testing.
    """
    if context.cap is None or not context.cap.isOpened():
        return None, None

    success, frame_bgr = context.cap.read()
    if not success:
        return None, None

    # Convert BGR (OpenCV) to RGB (for MediaPipe and Streamlit)
    frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
    image_height, image_width, _ = frame_rgb.shape

    # Run MediaPipe on this frame
    results = context.hands.process(frame_rgb)

    fingertip_positions: Optional[Dict[str, Tuple[float, float]]] = None

    if results.multi_hand_landmarks:
        # Use the first detected hand
        hand_landmarks = results.multi_hand_landmarks[0]

        # Extract fingertip coordinates
        fingertip_positions = _extract_fingertip_coords(
            hand_landmarks.landmark,
            image_width=image_width,
            image_height=image_height,
        )

        # Optionally draw landmarks on the frame
        if draw_landmarks:
            mp_drawing.draw_landmarks(
                frame_rgb,
                hand_landmarks,
                mp_hands.HAND_CONNECTIONS,
                mp_drawing_styles.get_default_hand_landmarks_style(),
                mp_drawing_styles.get_default_hand_connections_style(),
            )

    return fingertip_positions, frame_rgb
