"""
tests/integration/test_pipeline_integration.py

Integration tests for the ML pipeline modules (no camera needed).
Uses small synthetic images to test preprocessor, tracker, analyzer mocking.
"""

import numpy as np
import pytest

from app.pipeline.preprocessor import FramePreprocessor
from app.pipeline.tracker import FaceTracker
from app.pipeline.analyzer import EMOTION_COLORS

pytestmark = pytest.mark.asyncio


#  FramePreprocessor 

def test_preprocessor_decode_valid_jpeg():
    """Valid JPEG bytes should decode to a numpy array."""
    import cv2

    # Create a small solid-color image and encode as JPEG
    img = np.zeros((100, 100, 3), dtype=np.uint8)
    img[:] = (0, 128, 255)
    _, buf = cv2.imencode(".jpg", img)
    raw = buf.tobytes()

    preprocessor = FramePreprocessor()
    frame = preprocessor.decode(raw)
    assert frame is not None
    assert frame.shape[2] == 3


def test_preprocessor_decode_invalid_returns_none():
    preprocessor = FramePreprocessor()
    assert preprocessor.decode(b"not image bytes") is None


def test_preprocessor_resize_large_frame():
    """Frames larger than max_dim should be downscaled."""
    preprocessor = FramePreprocessor(max_dim=200)
    large_frame = np.zeros((1000, 1000, 3), dtype=np.uint8)
    result = preprocessor.resize_if_large(large_frame)
    assert max(result.shape[:2]) <= 200


def test_preprocessor_no_resize_small_frame():
    """Frames within max_dim should not be resized."""
    preprocessor = FramePreprocessor(max_dim=640)
    small = np.zeros((100, 100, 3), dtype=np.uint8)
    result = preprocessor.resize_if_large(small)
    assert result.shape == small.shape


#  FaceTracker 

def test_tracker_creates_new_track():
    tracker = FaceTracker()
    tracker.update([(10, 10, 50, 50)])
    results = tracker.get_results()
    assert len(results) == 1


def test_tracker_updates_existing_track():
    tracker = FaceTracker()
    tracker.update([(10, 10, 50, 50)])
    # Move face slightly (within CENTROID_THRESH)
    tracker.update([(15, 15, 50, 50)])
    results = tracker.get_results()
    assert len(results) == 1  # should still be one track


def test_tracker_default_emotion_is_neutral():
    tracker = FaceTracker()
    tracker.update([(10, 10, 50, 50)])
    results = tracker.get_results()
    assert results[0]["emotion"] == "neutral"


def test_tracker_adds_emotion():
    tracker = FaceTracker()
    tracker.update([(10, 10, 50, 50)])
    cx, cy = 35, 35
    tracker.add_emotion(cx, cy, "happy", {"happy": 90.0, "neutral": 10.0})
    results = tracker.get_results()
    assert results[0]["emotion"] == "happy"


def test_tracker_multiple_faces():
    tracker = FaceTracker()
    tracker.update([(0, 0, 50, 50), (300, 300, 50, 50)])
    results = tracker.get_results()
    assert len(results) == 2


#  EmotionAnalyzer colors 

def test_emotion_colors_all_defined():
    emotions = ["happy", "sad", "angry",
                "surprise", "fear", "disgust", "neutral"]
    for emo in emotions:
        assert emo in EMOTION_COLORS
        assert EMOTION_COLORS[emo].startswith("#")
