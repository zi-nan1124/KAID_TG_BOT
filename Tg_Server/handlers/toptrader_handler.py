# === handlers/toptrader_handler.py ===
from telegram import Update
from telegram.ext import ContextTypes
import asyncio
import pandas as pd
from io import StringIO
from concurrent.futures import ThreadPoolExecutor
from SOLONA.LIB.TopTrader import TopTraderFinder
from utils.safe_math import safe_float
from utils.format_utils import format_toptrader_table
import config

executor = ThreadPoolExecutor()

async def findtoptrader(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) != 1:
        await update.message.reply_text("用法：`/findtoptrader token_address`", parse_mode="Markdown")
        return

    token_address = context.args[0]
    await update.message.reply_text(f"正在获取 Token `{token_address}` 的顶级交易者...", parse_mode="Markdown")

    def blocking_task():
        finder = TopTraderFinder(api_key=config.CONFIG["BIRDEYE_APIKEY"])
        wallet_df = finder.get_wallets(token_address=token_address, limit=10)
        if wallet_df.empty:
            return None, None
        summary_df = finder.batch_calculate_profit_summary(wallet_df)
        return wallet_df, summary_df

    loop = asyncio.get_event_loop()
    wallet_df, summary_df = await loop.run_in_executor(executor, blocking_task)

    if wallet_df is None or summary_df is None or summary_df.empty:
        await update.message.reply_text("获取失败或没有数据。")
        return

    # 格式化展示表格
    preview_text = format_toptrader_table(summary_df)
    await update.message.reply_text(preview_text, parse_mode="Markdown")

    # 附带 CSV 文档
    csv_buffer = StringIO()
    summary_df.to_csv(csv_buffer, index=False)
    csv_buffer.seek(0)
    await update.message.reply_document(document=csv_buffer, filename="top_trader_summary.csv")
