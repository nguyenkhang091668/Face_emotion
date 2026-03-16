from __future__ import annotations
"""
app/pipeline/analyzer.py

DeepFace emotion analysis wrapper.
Runs analysis in a background thread (non-blocking) via a callback.
"""

import logging
import threading

import cv2
import numpy as np
from deepface import DeepFace

from app.core.config import settings

log = logging.getLogger(__name__)

EMOTION_COLORS: dict[str, str] = {
    "happy":    "#00DC5A",
    "sad":      "#C86432",
    "angry":    "#0032DC",
    "surprise": "#00D2FF",
    "fear":     "#9600C8",
    "disgust":  "#00B482",
    "neutral":  "#A0A0A0",
}


class EmotionAnalyzer:
    """
    Executes DeepFace.analyze in a daemon thread.
    Calls on_result(cx, cy, emotion, scores) when done.
    """

    def __init__(self):
        self._running = False

    @property
    def is_running(self) -> bool:
        return self._running

    def analyze_async(
        self,
        frame_bgr: np.ndarray,
        face_box: tuple[int, int, int, int],
        on_result,
    ) -> bool:
        """
        Non-blocking: spawn a thread to analyze the face ROI.
        Returns False if an analysis is already in progress.
        """
        if self._running:
            return False

        x, y, w, h = face_box
        face_roi = frame_bgr[y: y + h, x: x + w]
        if face_roi.size == 0:
            return False

        face_rgb = cv2.cvtColor(face_roi, cv2.COLOR_BGR2RGB)
        cx, cy = x + w // 2, y + h // 2

        self._running = True
        threading.Thread(
            target=self._run,
            args=(face_rgb, cx, cy, on_result),
            daemon=True,
        ).start()
        return True

    def _run(self, face_rgb: np.ndarray, cx: int, cy: int, on_result) -> None:
        try:
            result = DeepFace.analyze(
                face_rgb,
                actions=["emotion"],
                detector_backend=settings.DETECTOR_BACKEND,
                enforce_detection=False,
                silent=True,
            )
            data = result[0]
            emotion = data["dominant_emotion"]
            scores: dict[str, float] = data.get("emotion", {})
            on_result(cx, cy, emotion, scores)
        except Exception as exc:
            log.debug(f"DeepFace analysis error: {exc}")
        finally:
            self._running = False

    @staticmethod
    def get_color(emotion: str) -> str:
        return EMOTION_COLORS.get(emotion, "#C8C8C8")
