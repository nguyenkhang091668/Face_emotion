import cv2
import os
import time

output_dir = "dataset_test"
os.makedirs(output_dir, exist_ok=True)

cap = cv2.VideoCapture(0)

print("="*50)
print("AUTO CHỤP ẢNH MỖI 2 GIÂY (TỐI ĐA 100 ẢNH)")
print("- Bấm 'q' hoặc 'ESC' để thoát sớm.")
print("="*50)

count = 0
max_images = 100
last_capture_time = time.time()

while count < max_images:
    ret, frame = cap.read()
    if not ret:
        print("Không thể kết nối webcam.")
        break

    frame = cv2.flip(frame, 1)

    cv2.putText(frame, f"Da chup: {count}/{max_images}", (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

    cv2.imshow("Webcam - Auto Capture", frame)

    current_time = time.time()

    # Chụp mỗi 2 giây
    if current_time - last_capture_time >= 2:
        filename = os.path.join(output_dir, f"frame_{count:04d}.jpg")
        cv2.imwrite(filename, frame)
        print(f"Đã lưu: {filename}")
        count += 1
        last_capture_time = current_time

    key = cv2.waitKey(1) & 0xFF
    if key == ord('q') or key == 27:
        break

cap.release()
cv2.destroyAllWindows()

print(f"\n Hoàn thành! Đã chụp {count} ảnh.")
