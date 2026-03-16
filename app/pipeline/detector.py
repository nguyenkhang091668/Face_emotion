from __future__ import annotations
"""
app/pipeline/detector.py

MTCNN face detection wrapper.
Returns normalised bounding boxes at full resolution.
"""

import logging

import cv2
import numpy as np
from mtcnn import MTCNN

from app.core.config import settings

log = logging.getLogger(__name__)


class FaceDetector:
    """
    Wraps MTCNN to detect faces in a BGR frame.
    Detection runs on a downscaled copy for speed, then
    coordinates are scaled back to the original resolution.
    """

    def __init__(self, scale_factor: float = 0.5):
        log.info("Loading MTCNN detector …")
        self._detector = MTCNN()
        self._scale = scale_factor
        self._conf_threshold = settings.FACE_CONFIDENCE_THRESHOLD

    def detect(self, frame_bgr: np.ndarray) -> list[tuple[int, int, int, int]]:
        """
        Returns a list of (x, y, w, h) tuples in full-resolution coordinates.
        Filters detections below confidence threshold.
        """
        small = cv2.resize(frame_bgr, (0, 0), fx=self._scale, fy=self._scale)
        rgb_small = cv2.cvtColor(small, cv2.COLOR_BGR2RGB)

        try:
            detections = self._detector.detect_faces(rgb_small)
        except Exception as exc:
            log.error(f"MTCNN detection error: {exc}")
            return []

        inv = 1.0 / self._scale
        faces: list[tuple[int, int, int, int]] = []
        for d in detections:
            if d["confidence"] < self._conf_threshold:
                continue
            x, y, w, h = d["box"]
            x = max(0, int(x * inv))
            y = max(0, int(y * inv))
            w = int(w * inv)
            h = int(h * inv)
            faces.append((x, y, w, h))

        return faces
