from __future__ import annotations
"""
app/pipeline/preprocessor.py

Frame ingestion and validation.
Converts raw JPEG bytes → validated BGR ndarray.
"""

import logging

import cv2
import numpy as np

log = logging.getLogger(__name__)


class FramePreprocessor:
    """Decode, validate, and optionally resize incoming frames."""

    def __init__(self, max_dim: int = 1280):
        self.max_dim = max_dim

    def decode(self, raw_bytes: bytes) -> np.ndarray | None:
        """
        Decode JPEG/PNG bytes to BGR numpy array.
        Returns None if decoding fails.
        """
        try:
            arr = np.frombuffer(raw_bytes, dtype=np.uint8)
            frame = cv2.imdecode(arr, cv2.IMREAD_COLOR)
            if frame is None:
                log.warning("Failed to decode frame bytes")
            return frame
        except Exception as exc:
            log.error(f"Frame decode error: {exc}")
            return None

    def resize_if_large(self, frame: np.ndarray) -> np.ndarray:
        """Downscale frames that exceed max_dim on either axis."""
        h, w = frame.shape[:2]
        if max(h, w) > self.max_dim:
            scale = self.max_dim / max(h, w)
            new_w, new_h = int(w * scale), int(h * scale)
            frame = cv2.resize(frame, (new_w, new_h),
                               interpolation=cv2.INTER_AREA)
        return frame

    def process(self, raw_bytes: bytes) -> np.ndarray | None:
        """Full preprocessing pipeline: decode → validate → resize."""
        frame = self.decode(raw_bytes)
        if frame is None:
            return None
        return self.resize_if_large(frame)
