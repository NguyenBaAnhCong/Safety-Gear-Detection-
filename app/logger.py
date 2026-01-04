import cv2
import json
import os
from datetime import datetime


class ViolationLogger:
    def __init__(self, log_dir="logs"):
        self.log_dir = log_dir
        self.image_dir = os.path.join(log_dir, "images")
        self.json_path = os.path.join(log_dir, "violations.json")
        self.logged_ids = set()

        os.makedirs(self.image_dir, exist_ok=True)

        if not os.path.exists(self.json_path):
            with open(self.json_path, "w") as f:
                json.dump([], f)

    def log(self, frame, person_id, bbox, missing):
        if person_id in self.logged_ids:
            return

        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        x1, y1, x2, y2 = bbox

        # Crop ảnh person
        crop = frame[y1:y2, x1:x2]
        img_name = f"person_{person_id}_{timestamp}.jpg"
        img_path = os.path.join(self.image_dir, img_name)

        if crop.size > 0:
            cv2.imwrite(img_path, crop)

        record = {
            "person_id": person_id,
            "missing": missing,
            "time": timestamp,
            "image": img_name
        }

        # Ghi JSON
        with open(self.json_path, "r+") as f:
            data = json.load(f)
            data.append(record)
            f.seek(0)
            json.dump(data, f, indent=2)

        self.logged_ids.add(person_id)
