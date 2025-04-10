# === handlers/start_handler.py ===
from telegram import Update
from telegram.ext import ContextTypes

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "欢迎使用 Solana 钱包探索者！\n\n"
        "可用命令包括：\n"
        "`/profit 钱包地址` - 查询 7 日盈利\n"
        "`/decode 签名1 签名2 ...` - 解码交易\n"
        "`/findtoptrader token地址` - 查询 Token 的顶级交易者盈利",
        parse_mode="Markdown"
    )
