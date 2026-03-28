import cv2
import time
from app.pipeline.orchestrator import PipelineOrchestrator

def main():
    print("Khởi tạo PipelineOrchestrator...")
    orchestrator = PipelineOrchestrator()
    
    # Mở webcam (camera mặc định: 0) hoặc đường dẫn file video (ví dụ: 'video.mp4')
    # Ở đây dùng camera 0 để test trực tiếp
    cap = cv2.VideoCapture(0)
    
    if not cap.isOpened():
        print("Lỗi: Không thể mở được Camera.")
        return

    print("Bắt đầu Profiling! Nhấn 'q' trên cửa sổ video để thoát.")
    
    while True:
        ret, frame = cap.read()
        if not ret:
            print("Không đọc được frame. Dừng chương trình.")
            break
            
        # Đưa frame vào pipeline để xử lý
        results = orchestrator.process_frame(frame)
        
        # Hiển thị video để theo dõi trực quan
        cv2.imshow('Profiling Benchmark', frame)
        
        # Nhấn phím 'q' để thoát
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    # Phá hủy cửa sổ hiển thị
    cap.release()
    cv2.destroyAllWindows()
    print("Hoàn tất Profiling!")

if __name__ == "__main__":
    main()
