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

## Hướng dẫn Chạy Thử nghiệm (Evaluation)

Để chạy đánh giá mô hình trên tập dataset ảnh:

```bash
# Đảm bảo bạn đứng ở thư mục gốc của project (Xulyanhso)
venv/bin/python analysic/Task2_eval/picture_dataset.py
```

## Tư duy Nghiệp vụ (Data Science Logic) được áp dụng

Script `picture_dataset.py` không dùng cách dự đoán "nhắm mắt đưa chân" truyền thống mà đã được áp dụng các tư duy của một Data Scientist:

1. **Confidence Thresholding (Ngưỡng tự tin):**
    - Thay vì luôn luôn tin tưởng vào `dominant_emotion` trả về đầu tiên (Top-1), hệ thống có thiết lập một ngưỡng (ví dụ: `60%`).
    - Nếu tỷ lệ tự tin lớn nhất mà mô hình đưa ra nhỏ hơn ngưỡng này, kết quả sẽ bị đẩy vào nhóm `Uncertain` (Không chắc chắn). Thuật toán này giúp bảo vệ ứng dụng khỏi rủi ro do hiện tượng "Đoán mò" (Random Guessing).

2. **Confusion Matrix (Ma trận nhầm lẫn):**
    - Được trực quan hóa bằng `matplotlib` và `seaborn`.
    - Giúp người phân tích (DS) dễ dàng nhận ra các lỗi **sai lệch mang tính hệ thống** (Ví dụ: Thường xuyên nhầm lẫn giữa nhãn `Fear` (Sợ hãi) và `Sad` (Buồn bã)).

3. **Detector Backend:**
    - Script đánh giá độc lập mô hình với công cụ bắt khuôn mặt (Face Detection). Hiện tại mặc định sử dụng `mtcnn`. Có thể dễ dàng thay đổi sang `opencv` hoặc `ssd` để phù hợp với ngữ cảnh của dataset (cần vùng bao rộng hay hẹp).
