# 👷 AI Safety Gear Detection (Webcam Version)

> Hệ thống giám sát an toàn lao động (PPE) thời gian thực.

![Python](https://img.shields.io/badge/Python-3.8%2B-blue)
![YOLOv8](https://img.shields.io/badge/AI-YOLOv8-green)
![FastAPI](https://img.shields.io/badge/Backend-FastAPI-teal)
![Status](https://img.shields.io/badge/Status-Webcam%20Optimized-orange)

## 📖 Giới thiệu
Dự án này là hệ thống Computer Vision giúp tự động phát hiện và cảnh báo vi phạm an toàn lao động. Hệ thống sử dụng **YOLOv8** để nhận diện người và trang thiết bị, kết hợp với các **thuật toán hình học** để kiểm tra việc tuân thủ quy định.

Phiên bản này được tinh chỉnh đặc biệt để hoạt động tốt với **Camera Laptop (Webcam)**, tập trung vào giám sát phần thân trên của người lao động trong thời gian thực.

### 🎯 Đối tượng giám sát
Hệ thống tập trung kiểm tra 3 món đồ bảo hộ chính:
1.  **Mũ bảo hộ (Hardhat/Helmet):** Phải được đội trên đầu.
2.  **Áo phản quang (Safety Vest):** Phải được mặc trên người.
3.  **Găng tay (Gloves):** Phải xuất hiện trong khung hình.

---

## 💡 Tính năng kỹ thuật nổi bật

### 1. Webcam-Optimized Logic (Logic hình học)
Khác với các hệ thống CCTV góc rộng, hệ thống này sử dụng thuật toán chia tỷ lệ cơ thể động (Dynamic Body Splitting) phù hợp với góc quay ngang người của webcam:
* **Vùng đầu (Head Region):** 33% phía trên khung bao (Bounding Box) của người.
* **Vùng thân (Torso Region):** Phần còn lại phía dưới.
* **Cơ chế:** Mũ chỉ được tính là hợp lệ nếu tâm của nó nằm trong vùng "Head Region", tránh việc cầm mũ trên tay vẫn được tính là an toàn.

### 2. Anti-flickering Tracker (Chống nhiễu)
Tích hợp bộ theo dõi trạng thái (`tracker_state.py`) để giải quyết vấn đề nhấp nháy (flickering) của model AI:
* Hệ thống không báo lỗi ngay lập tức khi mất dấu vật thể trong 1-2 frame.
* Chỉ kích hoạt cảnh báo **UNSAFE** khi vi phạm tồn tại liên tiếp trong ngưỡng (Threshold) quy định (mặc định 5-8 frames).

### 3. Real-time Dashboard & Logging
* Backend **FastAPI** xử lý luồng video MJPEG stream mượt mà.
* Giao diện Web tự động hiển thị trạng thái **SAFE (Xanh)** hoặc **UNSAFE (Đỏ)**.
* **Tự động chụp ảnh bằng chứng** và lưu log JSON khi phát hiện vi phạm (Xử lý đa luồng không gây lag video).

---

## 🛠 Cài đặt & Sử dụng

### Bước 1: Clone và Cài đặt thư viện
```bash
# Clone dự án
git clone [https://github.com/NguyenBaAnhCong/Safety-Gear-Detection-.git](https://github.com/NguyenBaAnhCong/Safety-Gear-Detection-.git)
cd Safety-Gear-Detection-

# Tạo môi trường ảo (Khuyên dùng)
python -m venv venv
.\venv\Scripts\activate  # Windows
# source venv/bin/activate # Linux/Mac

# Cài đặt thư viện
pip install -r requirements.txt
```

### Bước 2: Khởi chạy hệ thống
Bạn cần mở 2 cửa sổ Terminal song song để chạy Backend và Frontend.

**Terminal 1: Chạy AI Backend**
```bash
uvicorn api.main:app --host 0.0.0.0 --port 8000
```
*Server sẽ khởi động và load model YOLOv8.*

**Terminal 2: Chạy Web Dashboard**
```bash
cd web
python -m http.server 3000
```

### Bước 3: Truy cập
* Mở trình duyệt và truy cập: `http://localhost:3000`
* Để truy cập từ các thiết bị khác (cùng Wifi): `http://<IP_MAY_TINH_CUA_BAN>:3000`

---

## 📂 Cấu trúc dự án

```text
PPE_Project/
├── api/
│   ├── main.py           # API Server & Endpoints
│   └── camera_service.py # Xử lý luồng Camera, tích hợp Tracker & Logger
├── app/
│   ├── detector.py       # YOLOv8 Inference
│   ├── ppe_logic.py      # Logic kiểm tra an toàn (Head/Torso check)
│   ├── body_parts.py     # Tính toán vùng cơ thể cho Webcam
│   ├── tracker_state.py  # Thuật toán chống nháy (State Machine)
│   └── logger.py         # Ghi log và lưu ảnh đa luồng
├── logs/                 # Thư mục lưu dữ liệu
│   ├── images/           # Ảnh chụp vi phạm
│   └── violations.json   # Log dữ liệu lịch sử
├── models/               # Chứa file weights
│   └── ppe_yolov8.pt     # Model AI (Weights)
├── web/                  # Giao diện Dashboard
│   └── index.html        # HTML/JS Client
├── scripts/              # Các script test độc lập
└── requirements.txt      # Danh sách thư viện
```

## 📊 Kết quả thực nghiệm
Nhóm đã thực hiện huấn luyện và đánh giá model với các thông số:
* **Dataset:** 3900 ảnh từ Roboflow Universe. ([link](https://universe.roboflow.com/site-construction-safety/site-construction-safety))
* **Model:** YOLOv8 Nano .
* **Độ chính xác (mAP@50):** > 0.90.
* **Tốc độ:** ~10-15 FPS (CPU i5).

*Đồ án môn học Thị Giác Máy Tính - 2024*
