import cv2
import threading
import time
from app.detector import YOLODetector
from app.ppe_logic import check_ppe

# --- IMPORT MỚI: Thêm Tracker và Logger ---
from app.tracker_state import PersonState
from app.logger import ViolationLogger

class CameraService:
    def __init__(self, model_path):
        self.detector = YOLODetector(model_path, conf=0.4)
        self.cap = None
        self.running = False
        
        # --- KHỞI TẠO MỚI ---
        self.tracker = PersonState()       # Bộ nhớ theo dõi trạng thái người
        self.logger = ViolationLogger()    # Bộ ghi log và chụp ảnh
        
        # Biến lưu kết quả JSON
        self.last_result = {
            "persons": [],
            "ppe_detections": []
        }
        
        # Biến lưu khung hình stream
        self.frame_bytes = None 
        self.thread = None

    def start(self, source=0):
        if self.running:
            return
        
        # Lưu ý: Nếu source là số (0, 1) thì là webcam
        # Nếu là string ("rtsp://...") thì là camera IP
        self.cap = cv2.VideoCapture(source)
        self.running = True
        self.thread = threading.Thread(target=self._loop, daemon=True)
        self.thread.start()

    def _loop(self):
        while self.running:
            ret, frame = self.cap.read()
            if not ret:
                time.sleep(0.1)
                continue

            # --- 1. PHÁT HIỆN ---
            detections = self.detector.detect(frame)
            persons = [d for d in detections if d["label"].lower() == "person"]
            ppes = [d for d in detections if d["label"].lower() != "person"]

            person_results = []
            
            for p in persons:
                # Kiểm tra logic an toàn (hiện tại)
                r = check_ppe(p, ppes)
                person_id = p.get("id", -1)

                # --- 2. LOGIC TRACKER (CHỐNG NHÁY) ---
                # Kiểm tra xem ngay lúc này có thiếu đồ không
                is_missing_now = (len(r["missing"]) > 0)
                
                # Cập nhật vào bộ theo dõi
                self.tracker.update(person_id, is_missing_now)
                
                # Chỉ coi là vi phạm thật sự nếu thiếu đồ liên tiếp trong 'threshold' frames
                # threshold=8 nghĩa là khoảng 0.5 giây liên tục không thấy mũ/áo mới báo lỗi
                is_confirmed_unsafe = self.tracker.is_confirmed_violation(person_id, threshold=8)
                
                # Trạng thái hiển thị cuối cùng (An toàn hay không)
                final_safe_status = not is_confirmed_unsafe

                # --- 3. GHI LOG & CHỤP ẢNH TỰ ĐỘNG ---
                if is_confirmed_unsafe:
                    # Gọi logger để lưu ảnh (Hàm này đã có logic tránh lưu trùng lặp)
                    self.logger.log(frame, person_id, p['bbox'], r['missing'])

                person_results.append({
                    "person_id": person_id,
                    "bbox": p["bbox"],
                    "safe": final_safe_status, # Dùng trạng thái ổn định từ tracker
                    "missing": r["missing"],
                    "found": r["found_items"]
                })

            # Cập nhật kết quả JSON cho API
            self.last_result = {
                "persons": person_results,
                "ppe_detections": ppes
            }

# --- 4. VẼ HÌNH LÊN VIDEO ---
            # Vẽ đồ vật (Mũ, áo, găng tay)
            for ppe in ppes:
                label = ppe['label'].lower()
                
                # THÊM DÒNG NÀY: Nếu là giày thì không vẽ, cho đỡ rối mắt
                if "shoes" in label or "boot" in label:
                    continue
                    
                x1, y1, x2, y2 = ppe['bbox']
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 255), 2)
                cv2.putText(frame, ppe['label'], (x1, y1-5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)

            # Vẽ người (Xanh / Đỏ dựa trên kết quả tracker)
            for res in person_results:
                x1, y1, x2, y2 = res['bbox']
                
                if res['safe']:
                    color = (0, 255, 0) # Xanh lá (An toàn)
                    status_text = "SAFE"
                else:
                    color = (0, 0, 255) # Đỏ (Vi phạm)
                    status_text = "UNSAFE"

                label = f"ID:{res['person_id']} {status_text}"
                
                cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
                cv2.putText(frame, label, (x1, y1-10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

                # Nếu thiếu đồ, hiện dòng chữ đỏ
                if not res['safe']:
                    missing_text = "Missing: " + ", ".join(res['missing'])
                    cv2.putText(frame, missing_text, (x1, y2+20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)

            # --- 5. STREAM ---
            try:
                # Resize ảnh stream nhỏ lại chút cho nhẹ mạng (nếu cần)
                stream_frame = cv2.resize(frame, (800, 600)) 
                ret, buffer = cv2.imencode('.jpg', stream_frame)
                if ret:
                    self.frame_bytes = buffer.tobytes()
            except Exception as e:
                print(f"Error encoding: {e}")

            time.sleep(0.01) # Giảm tải CPU

    def get_result(self):
        return self.last_result

    def generate_frames(self):
        while self.running:
            if self.frame_bytes:
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + self.frame_bytes + b'\r\n')
            time.sleep(0.04) # Giới hạn khoảng 25 FPS cho web

    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join()
        if self.cap:
            self.cap.release()