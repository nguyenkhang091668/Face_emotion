import cv2
import threading
import numpy as np
from collections import deque, Counter
from deepface import DeepFace
from mtcnn import MTCNN

#  Cấu hình 
ANALYZE_EVERY_N_FRAMES = 6   # Phân tích cảm xúc mỗi N frame
SMOOTH_WINDOW = 8            # Vote cảm xúc trên N kết quả gần nhất
CENTROID_THRESH = 80         # Pixel tối đa để coi 2 mặt là cùng một người
DETECTOR_BACKEND = 'mtcnn'   # Backend chính xác hơn Haar Cascade

# Màu cho từng cảm xúc
EMOTION_COLORS = {
    'happy':    (0, 220, 90),
    'sad':      (200, 100, 50),
    'angry':    (0, 50, 220),
    'surprise': (0, 210, 255),
    'fear':     (150, 0, 200),
    'disgust':  (0, 180, 130),
    'neutral':  (160, 160, 160),
}

EMOTIONS_ALL = ['angry', 'disgust', 'fear', 'happy', 'sad', 'surprise', 'neutral']

#  Bộ phát hiện mặt MTCNN 
detector = MTCNN()

#  Trạng thái theo dõi mặt 
# tracks: list of { 'centroid': (cx,cy), 'box': (x,y,w,h),
#                   'history': deque[str], 'scores': deque[dict] }
tracks: list[dict] = []
lock = threading.Lock()
analysis_running = False
frame_count = 0


#  Tiện ích 
def centroid(x, y, w, h):
    return (x + w // 2, y + h // 2)


def dist(a, b):
    return np.hypot(a[0] - b[0], a[1] - b[1])


def find_track(cx, cy):
    """Trả về track gần nhất với centroid (cx,cy), hoặc None nếu quá xa."""
    best, best_d = None, CENTROID_THRESH
    for t in tracks:
        d = dist(t['centroid'], (cx, cy))
        if d < best_d:
            best, best_d = t, d
    return best


def smoothed_emotion(track):
    """Cảm xúc dominant sau khi vote trên cửa sổ lịch sử."""
    history = track['history']
    if not history:
        return 'neutral', {}
    counter = Counter(history)
    dominant = counter.most_common(1)[0][0]

    # Trung bình điểm tin cậy
    avg_scores = {}
    if track['scores']:
        for emo in EMOTIONS_ALL:
            vals = [s[emo] for s in track['scores'] if emo in s]
            avg_scores[emo] = np.mean(vals) if vals else 0.0
    return dominant, avg_scores


#  Hàm phân tích chạy trong thread phụ 
def analyze_face(face_rgb, cx, cy):
    global analysis_running
    try:
        result = DeepFace.analyze(
            face_rgb,
            actions=['emotion'],
            detector_backend=DETECTOR_BACKEND,
            enforce_detection=False,
            silent=True
        )
        data = result[0]
        emotion = data['dominant_emotion']
        scores  = data.get('emotion', {})   # dict {emotion: confidence%}

        with lock:
            track = find_track(cx, cy)
            if track is not None:
                track['history'].append(emotion)
                track['scores'].append(scores)
    except Exception:
        pass
    finally:
        analysis_running = False


#  Camera 
cap = cv2.VideoCapture(0)

while True:
    ret, frame = cap.read()
    if not ret:
        break

    frame_count += 1
    display = frame.copy()

    # Phát hiện mặt bằng MTCNN (chạy trên frame gốc, chính xác hơn)
    small = cv2.resize(frame, (0, 0), fx=0.5, fy=0.5)
    rgb_small = cv2.cvtColor(small, cv2.COLOR_BGR2RGB)
    detections = detector.detect_faces(rgb_small)

    # Quy đổi tọa độ về frame gốc
    faces_full = []
    for d in detections:
        if d['confidence'] < 0.85:
            continue
        x, y, w, h = d['box']
        x, y = max(0, x * 2), max(0, y * 2)
        w, h = w * 2, h * 2
        faces_full.append((x, y, w, h))

    #  Cập nhật tracks 
    with lock:
        matched_tracks = set()
        for (x, y, w, h) in faces_full:
            cx, cy = centroid(x, y, w, h)
            track = find_track(cx, cy)
            if track is None:
                # Tạo track mới
                new_track = {
                    'centroid': (cx, cy),
                    'box': (x, y, w, h),
                    'history': deque(maxlen=SMOOTH_WINDOW),
                    'scores':  deque(maxlen=SMOOTH_WINDOW),
                }
                tracks.append(new_track)
            else:
                track['centroid'] = (cx, cy)
                track['box'] = (x, y, w, h)
                matched_tracks.add(id(track))

        # Xóa tracks không còn mặt nào gắn
        to_remove = [t for t in tracks
                     if id(t) not in matched_tracks and t not in
                     [find_track(*centroid(*b)) for b in faces_full]]
        for t in to_remove:
            if t in tracks:
                tracks.remove(t)

    #  Gửi phân tích sense mỗi N frame 
    if frame_count % ANALYZE_EVERY_N_FRAMES == 0 and not analysis_running and faces_full:
        x, y, w, h = faces_full[0]
        cx, cy = centroid(x, y, w, h)
        face_roi = frame[y:y+h, x:x+w]
        if face_roi.size > 0:
            face_rgb = cv2.cvtColor(face_roi, cv2.COLOR_BGR2RGB)
            analysis_running = True
            threading.Thread(
                target=analyze_face,
                args=(face_rgb, cx, cy),
                daemon=True
            ).start()

    #  Vẽ kết quả 
    with lock:
        for track in tracks:
            x, y, w, h = track['box']
            emotion, avg_scores = smoothed_emotion(track)
            color = EMOTION_COLORS.get(emotion, (200, 200, 200))

            # Khung mặt
            cv2.rectangle(display, (x, y), (x+w, y+h), color, 2)

            # Nhãn cảm xúc
            label = emotion if emotion != 'neutral' else 'neutral'
            (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.85, 2)
            cv2.rectangle(display, (x, y - th - 14), (x + tw + 8, y), color, -1)
            cv2.putText(display, label, (x + 4, y - 6),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.85, (255, 255, 255), 2)
            # Thanh confidence cho top-3 cảm xúc
            if avg_scores:
                sorted_emos = sorted(avg_scores.items(), key=lambda e: e[1], reverse=True)[:3]
                bar_x = x + w + 8
                bar_y = y
                bar_w, bar_h = 100, 16
                for i, (emo, score) in enumerate(sorted_emos):
                    by = bar_y + i * (bar_h + 4)
                    fill = int(bar_w * score / 100)
                    c = EMOTION_COLORS.get(emo, (200, 200, 200))
                    cv2.rectangle(display, (bar_x, by), (bar_x + bar_w, by + bar_h), (50, 50, 50), -1)
                    cv2.rectangle(display, (bar_x, by), (bar_x + fill, by + bar_h), c, -1)
                    cv2.putText(display, f"{emo[:3]} {score:.0f}%",
                                (bar_x + 2, by + bar_h - 3),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.38, (255, 255, 255), 1)

    cv2.imshow("Real-time Emotion Detection", display)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()