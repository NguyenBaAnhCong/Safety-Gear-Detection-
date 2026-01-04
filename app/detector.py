from ultralytics import YOLO

class YOLODetector:
    def __init__(self, model_path, conf=0.4, iou=0.5, device="cpu"):
        self.model = YOLO(model_path)
        self.conf = conf
        self.iou = iou
        self.device = device

    def detect(self, frame):
        results = self.model.track(
            source=frame,
            persist=True,
            conf=self.conf,
            iou=self.iou,
            device=self.device,
            verbose=False
        )

        detections = []

        for r in results:
            if r.boxes is None or r.boxes.id is None:
                continue

            for box, cls, tid, conf in zip(
                r.boxes.xyxy,
                r.boxes.cls,
                r.boxes.id,
                r.boxes.conf
            ):
                label = self.model.names[int(cls)]
                detections.append({
                    "id": int(tid),
                    "label": label,
                    "bbox": box.cpu().numpy().astype(int).tolist(),
                    "conf": float(conf)
                })

        return detections
