from __future__ import annotations
"""
app/pipeline/orchestrator.py

PipelineOrchestrator — composes the full ML pipeline:
  bytes → FramePreprocessor → FaceDetector → FaceTracker → EmotionAnalyzer → output
Replaces the monolithic EmotionEngine from app/emotion_engine.py.
"""
import time
import numpy as np

from app.core.config import settings
from app.pipeline.analyzer import EmotionAnalyzer
from app.pipeline.detector import FaceDetector
from app.pipeline.preprocessor import FramePreprocessor
from app.pipeline.tracker import FaceTracker

class PipelineOrchestrator:
    """
    Thread-safe, stateful pipeline for one camera stream.

    Usage:
        orchestrator = PipelineOrchestrator()
        results = orchestrator.process_bytes(jpeg_bytes)
        # results: list[{box, emotion, color, scores}]

        # Or if frame_bgr already decoded:
        results = orchestrator.process_frame(frame_bgr)
    """

    def __init__(self):
        self._preprocessor = FramePreprocessor()
        self._detector = FaceDetector()
        self._tracker = FaceTracker()
        self._analyzer = EmotionAnalyzer()
        self._frame_count = 0

    #  Public API

    def process_bytes(self, raw_bytes: bytes) -> list[dict]:
        """Full pipeline: decode bytes → process frame."""
        frame = self._preprocessor.process(raw_bytes)
        if frame is None:
            return []
        return self.process_frame(frame)

    def process_frame(self, frame_bgr: np.ndarray) -> list[dict]:
        """
        Process a BGR frame through the full pipeline.
        Returns list of:
            {
              "box":     [x, y, w, h],
              "emotion": str,
              "color":   "#RRGGBB",
              "scores":  {emotion: float, ...}  # top-3
            }
        """
        self._frame_count += 1
        time_total_start = time.perf_counter()

        # 1. Detect faces
        time_dect_start = time.perf_counter()
        faces = self._detector.detect(frame_bgr)
        time_dect_end = time.perf_counter()

        # 2. Update tracker
        time_str_start = time.perf_counter()
        self._tracker.update(faces)
        time_str_end = time.perf_counter()

        # 3. Schedule async emotion analysis every N frames
        analyze_interval = settings.ANALYZE_EVERY_N_FRAMES
        if (
            self._frame_count % analyze_interval == 0
            and not self._analyzer.is_running
            and faces
        ):
            x, y, w, h = faces[0]
            self._analyzer.analyze_async(
                frame_bgr,
                face_box=(x, y, w, h),
                on_result=self._tracker.add_emotion,
            )

        # 4. Build output from tracker state
        raw_results = self._tracker.get_results()
        output = []
        for r in raw_results:
            top3 = dict(
                sorted(r["scores"].items(),
                       key=lambda e: e[1], reverse=True)[:3]
            )
            output.append({
                "box":     r["box"],
                "emotion": r["emotion"],
                "color":   EmotionAnalyzer.get_color(r["emotion"]),
                "scores":  top3,
            })
        time_total_end = time.perf_counter()
        det_ms = (time_dect_end - time_dect_start) * 1000
        trk_ms = (time_str_end - time_str_start) * 1000
        total_ms = (time_total_end - time_total_start) * 1000

        print(f"Frame {self._frame_count:04d} | "
              f"MTCNN Detect: {det_ms:.1f}ms | Tracker: {trk_ms:.1f}ms | "
              f"Tổng FPS nhẩm tính: {1000 / total_ms:.1f} FPS")
        return output

    @property
    def frame_count(self) -> int:
        return self._frame_count

