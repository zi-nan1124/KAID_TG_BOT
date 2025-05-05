import requests
import pandas as pd
import time
import os
from datetime import datetime

class BlockBeatsFlashFetcher:
    def __init__(self, output_file="blockbeats_flash.csv", max_pages=2, page_size=50, sleep_sec=0.2):
        self.api_url = "https://api.theblockbeats.news/v1/open-api/open-flash"
        self.output_file = output_file
        self.max_pages = max_pages
        self.page_size = page_size
        self.sleep_sec = sleep_sec

    def _convert_timestamp(self, ts):
        try:
            ts = int(ts)
            return datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S")
        except Exception:
            return ts

    def fetch(self) -> pd.DataFrame:
        print("🚀 开始批量拉取律动快讯...")
        all_flash_records = []

        for page in range(1, self.max_pages + 1):
            params = {
                "page": page,
                "size": self.page_size,
                "lang": "cn"
            }
            print(f"\n🌐 正在请求第 {page} 页: {self.api_url} {params}")
            try:
                resp = requests.get(self.api_url, params=params)
                if resp.status_code != 200:
                    print(f"❌ 第 {page} 页请求失败: {resp.status_code}")
                    break
                data = resp.json()
                news_list = data.get("data", {}).get("data", [])

                if not isinstance(news_list, list):
                    print(f"⚠️ 第 {page} 页 data 格式异常，跳过")
                    break

                if not news_list:
                    print(f"✅ 拉取完毕，第 {page} 页为空")
                    break

                for item in news_list:
                    if isinstance(item, dict):
                        all_flash_records.append({
                            "id": item.get("id"),
                            "title": item.get("title"),
                            "content": item.get("content"),
                            "pic": item.get("pic"),
                            "link": item.get("link"),
                            "url": item.get("url"),
                            "create_time": item.get("create_time")
                        })

                print(f"✅ 第 {page} 页提取成功，本页 {len(news_list)} 条，累计 {len(all_flash_records)} 条")
                time.sleep(self.sleep_sec)
            except Exception as e:
                print(f"⚠️ 请求第 {page} 页失败: {e}")
                break

        new_df = pd.DataFrame(all_flash_records)

        if os.path.exists(self.output_file):
            existing_df = pd.read_csv(self.output_file, dtype={"id": int})
            print(f"\n📂 检测到已有 {self.output_file}，原数据 {len(existing_df)} 条")
            combined_df = pd.concat([existing_df, new_df], ignore_index=True)
        else:
            print(f"\n📂 未检测到已有文件，将直接保存")
            combined_df = new_df

        combined_df = combined_df.drop_duplicates(subset="id", keep="first")
        combined_df["create_time"] = combined_df["create_time"].apply(self._convert_timestamp)
        combined_df = combined_df.sort_values(by="create_time", ascending=False)
        combined_df.to_csv(self.output_file, index=False, encoding="utf-8-sig")

        print(f"\n📄 全部数据已保存为 {self.output_file}，当前总条数 {len(combined_df)} 条")
        print("\n🎯 所有页拉取完成！")

        return combined_df

if __name__ == "__main__":
    fetcher = BlockBeatsFlashFetcher(max_pages=5)
    df = fetcher.fetch()
    print(df.head())
