import json
import os


class DatabaseManager:
    _instance = None

    def __new__(cls, base_dir: str):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.base_dir = base_dir
        return cls._instance
    
    def load(self, filename: str, default):
        path = os.path.join(self.base_dir, "data", filename)
        if not os.path.exists(path):
            return default
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
        
    def save(self, filename: str, data):
        path = os.path.join(self.base_dir, "data", filename)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
