import json


class JsonWriter:
    def __init__(self, save_path: str):
        self.save_path = save_path

    def write(self, session_state):
        with open(self.save_path, "w", encoding="utf-8") as f:
            json.dump(session_state.to_dict(), f, ensure_ascii=False, indent=2)