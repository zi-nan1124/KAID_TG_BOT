# Tg_Server/handlers/alpha_handler.py

from telegram import Update
from telegram.ext import ContextTypes
import pandas as pd
import os

from config import CONFIG
from SOLONA.LIB.alpha.fetch_token_by_24V_BirdEye import BirdEyeFetcher
from Tg_Server.utils.format_utils import format_alpha_table


ALPHA_CSV_PATH = os.path.join(CONFIG["tg_server_data_path"], "alpha.csv")

def load_alpha_history() -> set:
    if os.path.exists(ALPHA_CSV_PATH):
        df = pd.read_csv(ALPHA_CSV_PATH)
        return set(df['address'].str.lower().tolist())  # ✅ 小写处理
    return set()


async def alpha_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔍 正在查询 BirdEye 数据，请稍候...")

    # 获取数据
    fetcher = BirdEyeFetcher(api_key=CONFIG["BIRDEYE_APIKEY"])
    df = fetcher.fetch_all()

    # 去重
    old_addresses = load_alpha_history()
    # 将历史地址统一小写
    old_addresses_lower = {addr.lower() for addr in old_addresses}
    # 将 df["address"] 转成小写后再做 isin
    df_new = df[~df["address"].str.lower().isin(old_addresses_lower)]

    if df_new.empty:
        await update.message.reply_text("✅ 没有发现新地址，一切如常。")
        return

    # 输出格式化：单位用 M
    msg = format_alpha_table(df_new, max_rows=20)
    await update.message.reply_text(msg, parse_mode="MarkdownV2")



