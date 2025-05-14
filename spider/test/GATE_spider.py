import pandas as pd
from playwright.sync_api import sync_playwright
import time

def scrape_gate_alpha_announcements():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        page.goto("https://www.gate.io/zh/announcements")
        page.wait_for_load_state('networkidle')

        # 滚动加载
        for _ in range(5):
            page.mouse.wheel(0, 150)
            time.sleep(1)

        # 提取纯文本
        plain_text = page.inner_text("body")
        browser.close()

        # 过滤包含 Gate.io Alpha 的行
        lines = plain_text.splitlines()
        alpha_lines = [line.strip() for line in lines if "gate.io alpha" in line.lower()]

        if not alpha_lines:
            print("❗ 未找到相关内容")
            return

        # 保存为 DataFrame，一行一条数据
        df = pd.DataFrame({"text": alpha_lines})
        print(df)

        # 保存 CSV（可选）
        df.to_csv("alpha_announcements.csv", index=False, encoding="utf-8-sig")
        print("\n✅ 已保存至 alpha_announcements.csv")

        return df

if __name__ == "__main__":
    scrape_gate_alpha_announcements()
