import cv2
import sys
import os
import time

# --- 1. SỬA LỖI ĐƯỜNG DẪN IMPORT ---
# Thêm thư mục gốc (parent directory) vào sys.path để Python nhìn thấy thư mục 'app'
# Nếu file này nằm trong thư mục 'scripts/', lệnh này sẽ trỏ về thư mục gốc dự án
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

from app.detector import YOLODetector
from app.ppe_logic import check_ppe
from app.tracker_state import PersonState
from app.logger import ViolationLogger

def main():
    # Lưu ý đường dẫn model: Vì chạy từ root hoặc script, nên dùng đường dẫn tuyệt đối hoặc tương đối chuẩn
    model_path = os.path.join(parent_dir, "models", "ppe_yolov8.pt")
    
    print(f"Đang tải model từ: {model_path} ...")
    detector = YOLODetector(model_path, conf=0.4)
    
    # Mở webcam (0)
    cap = cv2.VideoCapture(0)
    
    # Cài đặt độ phân giải hiển thị (nếu cần)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

    state = PersonState()
    logger = ViolationLogger(log_dir=os.path.join(parent_dir, "logs")) # Trỏ log về đúng chỗ

    print("Đang chạy camera... Nhấn 'q' để thoát.")

    prev_time = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Không đọc được camera!")
            break

        # Tính FPS
        curr_time = time.time()
        fps = 1 / (curr_time - prev_time) if prev_time > 0 else 0
        prev_time = curr_time

        # 1. Phát hiện vật thể
        detections = detector.detect(frame)

        persons = [d for d in detections if d["label"].lower() == "person"]
        ppes = [d for d in detections if d["label"].lower() != "person"]

        # 2. Vẽ các đồ bảo hộ (Mũ, Áo...) màu Vàng để dễ nhìn
        for ppe in ppes:
            x1, y1, x2, y2 = ppe["bbox"]
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 255), 2)
            cv2.putText(frame, ppe['label'], (x1, y1 - 5), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)

        # 3. Xử lý logic từng người
        for p in persons:
            person_id = p.get("id")
            
            # Nếu chưa có ID (do YOLO chưa track kịp), tạm bỏ qua hoặc gán ID tạm
            if person_id is None:
                continue

            result = check_ppe(p, ppes)
            
            # Logic Tracker (Chống nháy)
            is_violation_now = (len(result["missing"]) > 0)
            state.update(person_id, is_violation_now)
            
            # Chỉ báo đỏ khi vi phạm liên tiếp 5 frame (threshold)
            confirmed_violation = state.is_confirmed_violation(person_id, threshold=5)

            x1, y1, x2, y2 = p["bbox"]

            # Xác định màu sắc và nội dung hiển thị
            if confirmed_violation:
                color = (0, 0, 255) # Đỏ
                status_text = f"ID:{person_id} VIOLATION"
                
                # Ghi log (Chụp ảnh)
                # Lưu ý: Trong test desktop, cẩn thận kẻo nó chụp đầy ổ cứng
                # Chỉ log khi mới chuyển trạng thái (bạn có thể thêm logic này vào logger sau)
                logger.log(frame, person_id, p["bbox"], result["missing"])
                
            elif not is_violation_now:
                color = (0, 255, 0) # Xanh lá
                status_text = f"ID:{person_id} SAFE"
            else:
                color = (0, 255, 255) # Vàng (Đang check/Chưa ổn định)
                status_text = f"ID:{person_id} CHECKING"

            # Vẽ khung người
            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
            
            # Vẽ Header nền đen cho chữ dễ đọc
            (w, h), _ = cv2.getTextSize(status_text, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)
            cv2.rectangle(frame, (x1, y1 - 20), (x1 + w, y1), color, -1)
            cv2.putText(frame, status_text, (x1, y1 - 5), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

            # Vẽ danh sách đồ thiếu (Quan trọng để debug)
            if result["missing"]:
                missing_str = "Thieu: " + ", ".join(result["missing"])
                cv2.putText(frame, missing_str, (x1, y2 + 20), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)

        # Hiển thị FPS góc trái trên
        cv2.putText(frame, f"FPS: {int(fps)}", (10, 30), 
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

        cv2.imshow("TEST SYSTEM (Press Q to Exit)", frame)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()