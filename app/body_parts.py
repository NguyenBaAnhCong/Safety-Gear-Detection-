def get_body_parts(person_bbox):
    x1, y1, x2, y2 = person_bbox
    h = y2 - y1

    # ĐIỀU CHỈNH TỈ LỆ CHO WEBCAM (Góc quay cận cảnh)
    # - Đầu: Lấy 1/3 phía trên (Webcam thường quay đầu to hơn)
    # - Thân: Lấy phần còn lại bên dưới
    
    return {
        # Vùng đầu: Từ đỉnh đầu xuống 33% chiều cao khung hình
        "head":  (x1, y1, x2, y1 + int(0.33 * h)),
        
        # Vùng thân: Từ cổ (33%) xuống hết bên dưới (vì không quay chân)
        "torso": (x1, y1 + int(0.33 * h), x2, y2)
        
        # Đã bỏ vùng "feet" (chân) vì không cần thiết nữa
    }

def bbox_center(bbox):
    x1, y1, x2, y2 = bbox
    return ((x1 + x2) // 2, (y1 + y2) // 2)

def inside(box, point):
    x1, y1, x2, y2 = box
    px, py = point
    return x1 <= px <= x2 and y1 <= py <= y2