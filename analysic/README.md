# Phân Hệ Đánh Giá Cảm Xúc (Emotion Analysis Module)

Thư mục này chứa các mã nguồn phục vụ việc chạy thực nghiệm (evaluation) và đánh giá độ chính xác của các mô hình nhận diện cảm xúc khuôn mặt, đặc biệt tập trung vào thư viện **DeepFace**.

## Cấu trúc thư mục hiện tại

- `Task2_eval/picture_dataset.py`: Script dùng để chạy đánh giá hàng loạt (batch inference) trên tập dữ liệu ảnh cắt sẵn. Output in ra báo cáo tổng hợp (Classification Report) và vẽ Ma trận nhầm lẫn (Confusion Matrix).
- `Task2_eval/capture_webcam.py`: Script dùng để test nhận diện cảm xúc thời gian thực (real-time) thông qua webcam.

## Yêu cầu Hệ thống (Requirements)

Cần có môi trường ảo (`venv`) được kích hoạt và cài đặt các thư viện phục vụ Data Science (DS):

```bash
venv/bin/pip install deepface scikit-learn matplotlib seaborn
```

## Chạy môi trường thử nghiệm (Evaluation)

Để chạy đánh giá mô hình trên tập dataset ảnh:

```bash
# Đảm bảo bạn đứng ở thư mục gốc của project (Xulyanhso)
venv/bin/python analysic/Task2_eval/picture_dataset.py
```

## Áp dụng

Script `picture_dataset.py` không dùng cách dự đoán "nhắm mắt đưa chân" truyền thống mà đã được áp dụng các tư duy của một Data Scientist:

1.  **Confidence Thresholding (Ngưỡng tự tin):**
    - Thay vì luôn luôn tin tưởng vào `dominant_emotion` trả về đầu tiên (Top-1), hệ thống có thiết lập một ngưỡng (ví dụ: `60%`).
    - Nếu tỷ lệ tự tin lớn nhất mà mô hình đưa ra nhỏ hơn ngưỡng này, kết quả sẽ bị đẩy vào nhóm `Uncertain` (Không chắc chắn). Thuật toán này giúp bảo vệ ứng dụng khỏi rủi ro do hiện tượng "Đoán mò" (Random Guessing).

2.  **Confusion Matrix (Ma trận nhầm lẫn):**
    - Được trực quan hóa bằng `matplotlib` và `seaborn`.
    - Giúp người phân tích (DS) dễ dàng nhận ra các lỗi **sai lệch mang tính hệ thống** (Ví dụ: Thường xuyên nhầm lẫn giữa nhãn `Fear` (Sợ hãi) và `Sad` (Buồn bã)).

3.  **Detector Backend:**
    - Script đánh giá độc lập mô hình với công cụ bắt khuôn mặt (Face Detection). Hiện tại mặc định sử dụng `mtcnn`. Có thể dễ dàng thay đổi sang `opencv` hoặc `ssd` để phù hợp với ngữ cảnh của dataset (cần vùng bao rộng hay hẹp).
4.  **Classification_report & Plot seaborn:**
    - **Kết quả báo cáo khi chưa giới hạn ngưỡng:**

| Cảm xúc (Emotion) | Precision | Recall | F1-Score | Support |
| :--- | :---: | :---: | :---: | :---: |
| angry | 0.40 | 0.39 | 0.39 | 70 |
| disgust | 0.94 | 0.23 | 0.37 | 70 |
| fear | 0.27 | 0.27 | 0.27 | 70 |
| happy | 0.59 | 0.80 | 0.68 | 70 |
| neutral | 0.36 | 0.51 | 0.43 | 70 |
| sad | 0.33 | 0.44 | 0.38 | 70 |
| surprise | 0.74 | 0.49 | 0.59 | 70 |
| **accuracy** | | | **0.45** | **490** |
| **macro avg** | 0.52 | 0.45 | 0.44 | 490 |
| **weighted avg** | 0.52 | 0.45 | 0.44 | 490 |

    - **Mô hình sau khi đã được tinh chỉnh (giới hạn ngưỡng tự tin lớn nhất < 60%):**

| Cảm xúc (Emotion) | Precision | Recall | F1-Score | Support |
| :--- | :---: | :---: | :---: | :---: |
| Uncertain | 0.00 | 0.00 | 0.00 | 0 |
| angry | 0.38 | 0.30 | 0.34 | 50 |
| disgust | 1.00 | 0.20 | 0.33 | 50 |
| fear | 0.31 | 0.22 | 0.26 | 50 |
| happy | 0.62 | 0.74 | 0.67 | 50 |
| neutral | 0.42 | 0.42 | 0.42 | 50 |
| sad | 0.25 | 0.24 | 0.24 | 50 |
| surprise | 0.81 | 0.42 | 0.55 | 50 |
| **accuracy** | | | **0.36** | **350** |
| **macro avg** | 0.47 | 0.32 | 0.35 | 350 |
| **weighted avg** | 0.54 | 0.36 | 0.40 | 350 |

