"""
emotion_engine.py

Core emotion-detection logic, refactored from main.py into a reusable class.
Used by the FastAPI WebSocket server.
"""

import threading
import numpy as np
import cv2
from collections import deque, Counter
from deepface import DeepFace
from mtcnn import MTCNN

#  Cấu hình 
ANALYZE_EVERY_N_FRAMES = 6   # Phân tích cảm xúc mỗi N frame
SMOOTH_WINDOW          = 8   # Vote cảm xúc trên N kết quả gần nhất
CENTROID_THRESH        = 80  # Pixel tối đa để coi 2 mặt là cùng một người
DETECTOR_BACKEND       = "mtcnn"

EMOTION_COLORS = {
    "happy":    "#00DC5A",
    "sad":      "#C86432",
    "angry":    "#0032DC",
    "surprise": "#00D2FF",
    "fear":     "#9600C8",
    "disgust":  "#00B482",
    "neutral":  "#A0A0A0",
}

EMOTIONS_ALL = ["angry", "disgust", "fear", "happy", "sad", "surprise", "neutral"]


class EmotionEngine:
    """Thread-safe, stateful emotion detector for a single camera stream."""

    def __init__(self):
        self.detector        = MTCNN()
        self.tracks: list[dict] = []
        self.lock            = threading.Lock()
        self.analysis_running = False
        self.frame_count     = 0

    #  Private helpers 

    @staticmethod
    def _centroid(x, y, w, h):
        return (x + w // 2, y + h // 2)

    @staticmethod
    def _dist(a, b):
        return np.hypot(a[0] - b[0], a[1] - b[1])

    def _find_track(self, cx, cy):
        best, best_d = None, CENTROID_THRESH
        for t in self.tracks:
            d = self._dist(t["centroid"], (cx, cy))
            if d < best_d:
                best, best_d = t, d
        return best

    @staticmethod
    def _smoothed_emotion(track):
        history = track["history"]
        if not history:
            return "neutral", {}
        counter  = Counter(history)
        dominant = counter.most_common(1)[0][0]
        avg_scores: dict[str, float] = {}
        if track["scores"]:
            for emo in EMOTIONS_ALL:
                vals = [s[emo] for s in track["scores"] if emo in s]
                avg_scores[emo] = float(np.mean(vals)) if vals else 0.0
        return dominant, avg_scores

    #  Analysis thread 

    def _analyze_face(self, face_rgb, cx, cy):
        try:
            result = DeepFace.analyze(
                face_rgb,
                actions=["emotion"],
                detector_backend=DETECTOR_BACKEND,
                enforce_detection=False,
                silent=True,
            )
            data    = result[0]
            emotion = data["dominant_emotion"]
            scores  = data.get("emotion", {})
            with self.lock:
                track = self._find_track(cx, cy)
                if track is not None:
                    track["history"].append(emotion)
                    track["scores"].append(scores)
        except Exception:
            pass
        finally:
            self.analysis_running = False

    #  Public API 

    def process_frame(self, frame_bgr: np.ndarray) -> list[dict]:
        """
        Process one BGR frame.
        Returns a list of dicts:
            {
              "box":     [x, y, w, h],
              "emotion": str,
              "color":   "#RRGGBB",
              "scores":  { emotion: float, ... }   # top-3 or empty
            }
        """
        self.frame_count += 1

        #  Detect faces on a downscaled copy 
        small     = cv2.resize(frame_bgr, (0, 0), fx=0.5, fy=0.5)
        rgb_small = cv2.cvtColor(small, cv2.COLOR_BGR2RGB)
        detections = self.detector.detect_faces(rgb_small)

        faces_full = []
        for d in detections:
            if d["confidence"] < 0.85:
                continue
            x, y, w, h = d["box"]
            x, y = max(0, x * 2), max(0, y * 2)
            w, h = w * 2, h * 2
            faces_full.append((x, y, w, h))

        #  Update centroid tracks 
        with self.lock:
            matched = set()
            for (x, y, w, h) in faces_full:
                cx, cy = self._centroid(x, y, w, h)
                track  = self._find_track(cx, cy)
                if track is None:
                    self.tracks.append({
                        "centroid": (cx, cy),
                        "box":      (x, y, w, h),
                        "history":  deque(maxlen=SMOOTH_WINDOW),
                        "scores":   deque(maxlen=SMOOTH_WINDOW),
                    })
                else:
                    track["centroid"] = (cx, cy)
                    track["box"]      = (x, y, w, h)
                    matched.add(id(track))

            # Prune stale tracks
            active_centres = {self._centroid(*b) for b in faces_full}
            self.tracks = [
                t for t in self.tracks
                if id(t) in matched
                or self._find_track(*t["centroid"]) is not None
                and t["centroid"] in active_centres
            ]

        #  Trigger async DeepFace analysis every N frames 
        if (
            self.frame_count % ANALYZE_EVERY_N_FRAMES == 0
            and not self.analysis_running
            and faces_full
        ):
            x, y, w, h = faces_full[0]
            cx, cy     = self._centroid(x, y, w, h)
            face_roi   = frame_bgr[y : y + h, x : x + w]
            if face_roi.size > 0:
                face_rgb = cv2.cvtColor(face_roi, cv2.COLOR_BGR2RGB)
                self.analysis_running = True
                threading.Thread(
                    target=self._analyze_face,
                    args=(face_rgb, cx, cy),
                    daemon=True,
                ).start()

        #  Build output 
        results = []
        with self.lock:
            for track in self.tracks:
                x, y, w, h       = track["box"]
                emotion, avg_scores = self._smoothed_emotion(track)
                top3 = dict(
                    sorted(avg_scores.items(), key=lambda e: e[1], reverse=True)[:3]
                )
                results.append({
                    "box":     [x, y, w, h],
                    "emotion": emotion,
                    "color":   EMOTION_COLORS.get(emotion, "#C8C8C8"),
                    "scores":  top3,
                })
        return results
