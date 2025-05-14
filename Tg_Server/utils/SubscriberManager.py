# Tg_Server/utils/subscriber_manager.py

import json
import os
from config import CONFIG

class SubscriberManager:
    def __init__(self, filename="subscribed_users.json"):
        self.directory = CONFIG.get("tg_server_data_path", ".")
        self.filepath = os.path.join(self.directory, filename)

        # 创建目录（如果不存在）
        os.makedirs(self.directory, exist_ok=True)
        self._load()

    def _load(self):
        if os.path.exists(self.filepath):
            try:
                with open(self.filepath, "r") as f:
                    self.subscribers = set(json.load(f))
            except (json.JSONDecodeError, ValueError) as e:
                print(f"⚠️ 订阅者文件解析失败，已重置为空列表: {e}")
                self.subscribers = set()
        else:
            self.subscribers = set()

    def _save(self):
        with open(self.filepath, "w") as f:
            json.dump(list(self.subscribers), f)

    def add(self, chat_id: int):
        if chat_id not in self.subscribers:
            self.subscribers.add(chat_id)
            self._save()

    def remove(self, chat_id: int):
        if chat_id in self.subscribers:
            self.subscribers.remove(chat_id)
            self._save()

    def get_all(self):
        return list(self.subscribers)

    def is_subscribed(self, chat_id: int):
        return chat_id in self.subscribers
