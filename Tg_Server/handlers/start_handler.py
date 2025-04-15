# Tg_Server/handlers/start_handler.py
from telegram import Update
from telegram.ext import ContextTypes
from Tg_Server.utils.SubscriberManager import SubscriberManager

subscriber_mgr = SubscriberManager()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    subscriber_mgr.add(chat_id)

    await update.message.reply_text(
        "欢迎使用 Solana 钱包探索者！\n\n"
        "可用命令包括：\n"
        "`/profit 钱包地址` - 查询 7 日盈利\n"
        "`/decode 签名1 签名2 ...` - 解码交易\n"
        "`/findtoptrader token地址` - 查询 Token 的顶级交易者盈利\n"
        "`/alpha` - 查询当前 BirdEye 热门 Token 并过滤已监控地址\n"
        "`/alpha_mute 地址 原因` - 将地址添加进监控屏蔽列表",
        parse_mode="Markdown"
    )
