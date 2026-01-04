from app.body_parts import get_body_parts, bbox_center, inside

# 1. CẬP NHẬT LUẬT: Chỉ giữ lại Mũ, Áo, Găng tay
PPE_RULES = {
    # Các loại mũ -> Kiểm tra ở vùng đầu (head)
    "helmet": "head",
    "hardhat": "head",
    "cap": "head",
    
    # Các loại áo -> Kiểm tra ở vùng thân (torso)
    "vest": "torso",
    "shirt": "torso",
    "jacket": "torso",
    
    # Găng tay -> Kiểm tra ở vùng toàn thân (body)
    # Lý do: Tay có thể giơ lên, hạ xuống, khó định vị cố định như đầu.
    # Nên chỉ cần găng tay nằm trong khung người là OK.
    "gloves": "body",
    "glove": "body" 
}

def check_ppe(person, ppes):
    # Lấy các vùng cơ thể (Đầu, Thân)
    body_parts = get_body_parts(person["bbox"])
    
    # Thêm vùng "body" (toàn bộ khung người) để check găng tay
    body_parts["body"] = person["bbox"]

    # Danh sách các món đồ cần tìm
    found = {
        "helmet": False,
        "vest": False,
        "gloves": False
    }

    for ppe in ppes:
        label = ppe["label"].lower()
        
        # Nếu nhãn không nằm trong luật (ví dụ: shoes), bỏ qua luôn
        if label not in PPE_RULES:
            continue

        target_part = PPE_RULES[label] # Ví dụ: helmet -> head
        
        # Lấy tâm của vật thể PPE
        center = bbox_center(ppe["bbox"])

        # Kiểm tra: Tâm vật thể có nằm trong vùng cơ thể tương ứng không?
        if inside(body_parts[target_part], center):
            if "helmet" in label or "hardhat" in label or "cap" in label:
                found["helmet"] = True
            elif "vest" in label or "shirt" in label or "jacket" in label:
                found["vest"] = True
            elif "glove" in label:
                found["gloves"] = True

    # Tìm những món bị thiếu (False)
    missing = [k for k, v in found.items() if not v]

    return {
        "safe": len(missing) == 0,
        "missing": missing,
        "found_items": found
    }