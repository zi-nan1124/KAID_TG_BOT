# === handlers/decode_handler.py ===
from telegram import Update
from telegram.ext import ContextTypes
import pandas as pd
from SOLONA.LIB.TransactionListDecoder import TransactionListDecoder

async def decode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("用法：`/decode tx1 tx2 ...`（支持多个交易签名）", parse_mode="Markdown")
        return

    sig_list = context.args
    await update.message.reply_text(f"收到 {len(sig_list)} 个交易签名，开始解析中...")

    try:
        df_signatures = pd.DataFrame({"signature": sig_list})
        decoder = TransactionListDecoder()
        final_result = decoder.decode(df_signatures)

        if final_result.empty:
            await update.message.reply_text("没有解析出任何交易数据。")
            return

        preview = final_result.head(5).to_markdown(index=False)
        message = f"解析完成，前 5 条结果：\n```\n{preview}\n```"
        await update.message.reply_text(message, parse_mode="Markdown")

    except Exception as e:
        await update.message.reply_text(f"解析出错：{e}")