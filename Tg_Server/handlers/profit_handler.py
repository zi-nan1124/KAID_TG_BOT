# === handlers/profit_handler.py ===
from telegram import Update
from telegram.ext import ContextTypes
from concurrent.futures import ThreadPoolExecutor
import asyncio
import config
from Tg_Server.utils.format_utils import format_profit_table
from SOLONA.LIB.Sol_Wallet_Fetcher import SolanaWalletExplorer

executor = ThreadPoolExecutor()

async def profit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) != 1:
        await update.message.reply_text("用法：`/profit 钱包地址`", parse_mode="Markdown")
        return

    wallet_address = context.args[0]
    await update.message.reply_text(f"开始分析地址: `{wallet_address}`，请稍等...", parse_mode="Markdown")

    def blocking_task():
        explorer = SolanaWalletExplorer(config.CONFIG["rpc_url"], wallet_address)
        return explorer.calculate_profit_by_7_day()

    loop = asyncio.get_event_loop()
    result_df, summary = await loop.run_in_executor(executor, blocking_task)

    if summary is None or result_df is None or result_df.empty:
        await update.message.reply_text("分析失败或交易数据为空。")
        return

    formatted = format_profit_table(result_df, summary)
    await update.message.reply_text(formatted, parse_mode="Markdown")
