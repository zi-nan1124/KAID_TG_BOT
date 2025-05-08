import os
import time
import pandas as pd
import sys
from bs4 import BeautifulSoup
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
from lark.larkapi.message_sender import message
from lark.config import pvp_url, BlockTime_Fetcher_keywords
from BlockBeats.BlockBeatsFlashFetcher import BlockBeatsFlashFetcher

class BlockTime_Fetcher:
    def __init__(self,
                 pvp_url=pvp_url,
                 BlockTime_Fetcher_keywords=BlockTime_Fetcher_keywords,
                 record_file: str = None):
        self.fetcher = BlockBeatsFlashFetcher()
        self.pvp_url = pvp_url
        self.BlockTime_Fetcher_keywords = BlockTime_Fetcher_keywords
        self.record_file = record_file or self._default_record_path()
        self._ensure_data_dir()
        self.sent_ids = self._load_sent_ids()

    @staticmethod
    def _default_record_path():
        # 获取 lark 目录的绝对路径（也就是 BlockTime_Fetcher 上一级的上一级）
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

    def _match_BlockTime_Fetcher_keywords(self, text: str) -> bool:
        return any(kw.lower() in text.lower() for kw in self.BlockTime_Fetcher_keywords)

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
            if self._match_BlockTime_Fetcher_keywords(row["title"]):
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
            content = f"📢 {item['title']}\n\n{clean_text}\n\n🔗 {item['url']}"
            result = message(self.pvp_url, content)
            if result["success"]:
                sent_ids.append(item["id"])
            else:
                print(f"❌ 消息发送失败: {result}")

        self._save_sent_ids(sent_ids)
        print(f"✅ 已发送并记录 {len(sent_ids)} 条快讯")


if __name__ == "__main__":
    notifier = BlockTime_Fetcher()
    notifier.run()  # ✅ 每隔10分钟自动运行
