import os
import time
import pandas as pd
from bs4 import BeautifulSoup

import config
from BlockBeats.BlockBeatsFlashFetcher import BlockBeatsFlashFetcher
from lark.larkapi.message_sender import LarkMessageSender
from lark.config import APP_ID, APP_SECRET, USERID, keywords,MESSAGE_PUSH_INTERVAL

class BNfetcher:
    def __init__(self,
                 app_id=APP_ID,
                 app_secret=APP_SECRET,
                 user_list=USERID,
                 keywords=keywords,
                 record_file: str = None):
        if record_file is None:
            record_file = self._default_record_path()

        self.fetcher = BlockBeatsFlashFetcher()
        self.sender = LarkMessageSender(app_id, app_secret)
        self.user_list = user_list
        self.keywords = keywords
        self.record_file = record_file
        self._ensure_data_dir()
        self.sent_ids = self._load_sent_ids()

    @staticmethod
    def _default_record_path():
        # 获取 lark 目录的绝对路径（也就是 BNfetcher 上一级的上一级）
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        return os.path.join(base_dir, "DATA", "sent_flash_ids.csv")

    def _ensure_data_dir(self):
        os.makedirs(os.path.dirname(self.record_file), exist_ok=True)

    def _load_sent_ids(self) -> set:
        if os.path.exists(self.record_file):
            df = pd.read_csv(self.record_file, dtype={"id": int})
            return set(df["id"].tolist())
        return set()

    def _save_sent_ids(self, new_ids: list[int]):
        if not new_ids:
            return
        new_df = pd.DataFrame({"id": new_ids})
        mode = 'a' if os.path.exists(self.record_file) else 'w'
        header = not os.path.exists(self.record_file)
        new_df.to_csv(self.record_file, mode=mode, index=False, header=header)

    def _match_keywords(self, text: str) -> bool:
        return any(kw.lower() in text.lower() for kw in self.keywords)

    def _html_to_text(self, html: str) -> str:
        """将 HTML 内容转为纯文本"""
        soup = BeautifulSoup(html or "", "html.parser")
        return soup.get_text(separator="\n").strip()

    def run(self):
        df = self.fetcher.fetch()
        to_send = []

        for _, row in df.iterrows():
            if row["id"] in self.sent_ids:
                continue
            if self._match_keywords(row["title"]):
                to_send.append({
                    "id": row["id"],
                    "title": row["title"],
                    "content": row["content"],
                    "url": row["url"] or row["link"]
                })

        print(f"🎯 共匹配到 {len(to_send)} 条快讯要发送")

        sent_ids = []

        for item in to_send:
            clean_text = self._html_to_text(item["content"])
            message = f"📢 {item['title']}\n\n{clean_text}\n\n🔗 {item['url']}"
            for user in self.user_list:
                self.sender.send_message(user, message)
            sent_ids.append(item["id"])

        self._save_sent_ids(sent_ids)
        print(f"✅ 全部快讯发送完毕，记录已更新")

    def run_forever(self, interval_sec: int = MESSAGE_PUSH_INTERVAL):
        print(f"🦖 FlashNewsNotifier 启动，每 {interval_sec // 60} 分钟执行一次")
        while True:
            try:
                self.run()
            except Exception as e:
                print(f"❌ run() 执行出错: {e}")
            time.sleep(interval_sec)


if __name__ == "__main__":
    notifier = BNfetcher()
    notifier.run_forever()  # ✅ 每隔10分钟自动运行
