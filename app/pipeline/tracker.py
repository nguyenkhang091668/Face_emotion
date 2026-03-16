from __future__ import annotations
"""
app/pipeline/tracker.py

Centroid-based face track manager.
Maintains identity continuity across frames by matching
new detections to the nearest existing track centroid.
"""

from collections import Counter, deque

import numpy as np

from app.core.config import settings

EMOTIONS_ALL = ["angry", "disgust", "fear",
                "happy", "sad", "surprise", "neutral"]


class FaceTracker:
    """
    Maintains a list of active face tracks.
    Each track stores:
      centroid, box, rolling history of emotions, rolling scores.
    """

    def __init__(self):
        self._tracks: list[dict] = []
        self._thresh = settings.CENTROID_THRESH
        self._smooth_window = settings.SMOOTH_WINDOW

    #  Private helpers 

    @staticmethod
    def _centroid(x: int, y: int, w: int, h: int) -> tuple[int, int]:
        return (x + w // 2, y + h // 2)

    @staticmethod
    def _dist(a: tuple, b: tuple) -> float:
        return float(np.hypot(a[0] - b[0], a[1] - b[1]))

    def _find_track(self, cx: int, cy: int) -> dict | None:
        best, best_d = None, self._thresh
        for t in self._tracks:
            d = self._dist(t["centroid"], (cx, cy))
            if d < best_d:
                best, best_d = t, d
        return best

    #  Public API 

    def update(self, faces: list[tuple[int, int, int, int]]) -> None:
        """Match detected faces to existing tracks; create new ones as needed."""
        matched_ids: set[int] = set()

        for (x, y, w, h) in faces:
            cx, cy = self._centroid(x, y, w, h)
            track = self._find_track(cx, cy)
            if track is None:
                self._tracks.append({
                    "centroid": (cx, cy),
                    "box": (x, y, w, h),
                    "history": deque(maxlen=self._smooth_window),
                    "scores": deque(maxlen=self._smooth_window),
                })
            else:
                track["centroid"] = (cx, cy)
                track["box"] = (x, y, w, h)
                matched_ids.add(id(track))

        # Prune stale tracks
        active_centroids = {self._centroid(*b) for b in faces}
        self._tracks = [
            t for t in self._tracks
            if id(t) in matched_ids or t["centroid"] in active_centroids
        ]

    def add_emotion(self, cx: int, cy: int, emotion: str, scores: dict) -> None:
        """Append emotion result to the nearest track."""
        track = self._find_track(cx, cy)
        if track is not None:
            track["history"].append(emotion)
            track["scores"].append(scores)

    def get_results(self) -> list[dict]:
        """
        Return current state of all tracks as:
          { "box": [x,y,w,h], "centroid": (cx,cy), "emotion": str, "scores": dict }
        """
        results = []
        for track in self._tracks:
            x, y, w, h = track["box"]
            emotion, avg_scores = self._smoothed_emotion(track)
            cx, cy = track["centroid"]
            results.append({
                "box": [x, y, w, h],
                "centroid": (cx, cy),
                "emotion": emotion,
                "scores": avg_scores,
            })
        return results

    def get_first_face(self) -> dict | None:
        """Return the first track (primary subject), or None."""
        return self._tracks[0] if self._tracks else None

    @staticmethod
    def _smoothed_emotion(track: dict) -> tuple[str, dict]:
        history = track["history"]
        if not history:
            return "neutral", {}
        dominant = Counter(history).most_common(1)[0][0]
        avg_scores: dict[str, float] = {}
        if track["scores"]:
            for emo in EMOTIONS_ALL:
                vals = [s[emo] for s in track["scores"] if emo in s]
                avg_scores[emo] = float(np.mean(vals)) if vals else 0.0
        return dominant, avg_scores
