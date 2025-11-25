import json
import os
from config import Config

class SimpleDB:
    def __init__(self):
        self.data_dir = Config.DATA_DIR
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
    
    def save(self, filename, data):
        filepath = os.path.join(self.data_dir, filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def load(self, filename):
        filepath = os.path.join(self.data_dir, filename)
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            return []
    
    def get_next_id(self, data_list):
        if not data_list:
            return 1
        return max(item['id'] for item in data_list) + 1