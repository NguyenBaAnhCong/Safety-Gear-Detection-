import time

class PersonState:
    def __init__(self):
        self.data = {}

    def update(self, person_id, is_violation):
        now = time.time()

        if person_id not in self.data:
            self.data[person_id] = {
                "first_seen": now,
                "violation_frames": 0,
                "last_seen": now
            }

        if is_violation:
            self.data[person_id]["violation_frames"] += 1
        else:
            self.data[person_id]["violation_frames"] = 0

        self.data[person_id]["last_seen"] = now

    def is_confirmed_violation(self, person_id, threshold=5):
        return self.data[person_id]["violation_frames"] >= threshold
