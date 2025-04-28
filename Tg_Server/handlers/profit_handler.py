from telegram import Update
from telegram.ext import ContextTypes
import config
from Tg_Server.utils.format_utils import format_profit_table
from SOLONA.LIB.Sol_Wallet_Fetcher import SolanaWalletExplorer
from SOLONA.LIB.Logger import Logger  # 假设你有通用日志类

logger = Logger()

async def profit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if len(context.args) != 1:
            await update.message.reply_text("用法：`/profit 钱包地址`", parse_mode="Markdown")
            return

        wallet_address = context.args[0]
        await update.message.reply_text(f"开始分析地址: `{wallet_address}`，请稍等...", parse_mode="Markdown")

        print(f"[DEBUG] handler triggered, address = {wallet_address}")

        explorer = SolanaWalletExplorer(config.CONFIG["rpc_url"], wallet_address)
        result_df, summary = await explorer.calculate_profit_by_7_day()

        if summary is None or result_df is None or result_df.empty:
            await update.message.reply_text("分析失败或交易数据为空。")
            return

        formatted = format_profit_table(result_df, summary)
        await update.message.reply_text(formatted, parse_mode="Markdown")

    except Exception as e:
        import traceback
        tb = traceback.format_exc()
        print(f"[ERROR] handler crashed: {e}\n{tb}")
        await update.message.reply_text("❌ 出现内部错误，日志已记录。")

