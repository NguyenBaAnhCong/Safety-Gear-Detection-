import cv2
import numpy as np
from fastapi import FastAPI, UploadFile, File
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware

# Import các module logic
from app.detector import YOLODetector
from app.ppe_logic import check_ppe
from api.camera_service import CameraService

app = FastAPI(
    title="PPE Detection API",
    description="Hệ thống phát hiện bảo hộ lao động (Ảnh & Camera)",
    version="2.0"
)

# --- CẤU HÌNH CORS (Quan trọng để Web gọi được API) ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Cho phép mọi nguồn truy cập (để test cho dễ)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- KHỞI TẠO ---
# 1. Khởi tạo Service quản lý Camera (cho tính năng quay video)
camera_service = CameraService("models/ppe_yolov8.pt")

# 2. Khởi tạo Detector riêng cho tính năng Upload ảnh
# (Tách riêng để không ảnh hưởng nếu camera đang chạy)
image_detector = YOLODetector("models/ppe_yolov8.pt", conf=0.4)


@app.get("/health")
def health():
    return {"status": "System is healthy"}


# ==========================================
# PHẦN 1: API XỬ LÝ ẢNH TĨNH (UPLOAD)
# ==========================================
@app.post("/detect/image")
async def detect_image(file: UploadFile = File(...)):
    # 1. Đọc ảnh từ client gửi lên
    contents = await file.read()
    np_arr = np.frombuffer(contents, np.uint8)
    img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

    if img is None:
        return {"error": "File ảnh không hợp lệ"}

    # 2. Phát hiện đối tượng
    detections = image_detector.detect(img)

    # 3. Phân loại
    persons = [d for d in detections if d["label"].lower() == "person"]
    ppes = [d for d in detections if d["label"].lower() != "person"]

    results = []

    # 4. Kiểm tra logic an toàn
    for p in persons:
        r = check_ppe(p, ppes)
        results.append({
            "person_id": p.get("id", -1),
            "bbox": p["bbox"],
            "safe": r["safe"],
            "missing": r["missing"],
            "found": r["found_items"]
        })

    # 5. Trả về kết quả (Cấu trúc giống Camera để dễ xử lý)
    return {
        "success": True,
        "num_persons": len(persons),
        "persons": results,         # Danh sách người và trạng thái
        "ppe_detections": ppes      # Danh sách đồ vật để vẽ hình
    }


# ==========================================
# PHẦN 2: API ĐIỀU KHIỂN CAMERA & STREAM
# ==========================================

@app.post("/camera/start")
def start_camera():
    """Bật camera (Webcam hoặc RTSP)"""
    # source=0 là webcam laptop. Nếu dùng camera IP, đổi thành link RTSP
    camera_service.start(source=0)
    return {"message": "Camera đã được bật"}


@app.post("/camera/stop")
def stop_camera():
    """Tắt camera để giải phóng tài nguyên"""
    camera_service.stop()
    return {"message": "Camera đã tắt"}


@app.get("/camera/result")
def get_camera_result():
    """Lấy dữ liệu JSON kết quả (dùng cho bảng thống kê bên phải)"""
    return camera_service.get_result()


@app.get("/video_feed")
def video_feed():
    """Stream hình ảnh video (dùng cho thẻ <img src=...> trên web)"""
    return StreamingResponse(
        camera_service.generate_frames(),
        media_type="multipart/x-mixed-replace;boundary=frame"
    )