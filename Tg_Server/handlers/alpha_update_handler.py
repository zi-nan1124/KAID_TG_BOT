# Tg_Server/handlers/alpha_update_handler.py

from telegram import Update
from telegram.ext import ContextTypes
import os
import pandas as pd

from config import CONFIG

ALPHA_CSV_PATH = os.path.join(CONFIG["tg_server_data_path"], "alpha.csv")


async def alpha_mute(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 2:
        await update.message.reply_text("❌ 用法：/alpha_mute 地址 原因")
        return

    address = context.args[0]
    reason = " ".join(context.args[1:])

    # 如果文件不存在就创建
    if not os.path.exists(ALPHA_CSV_PATH):
        df = pd.DataFrame(columns=["address", "reason"])
        df.to_csv(ALPHA_CSV_PATH, index=False)

    # 读取旧表
    df = pd.read_csv(ALPHA_CSV_PATH)

    # 如果已经存在该地址就更新 reason，否则添加新行
    if address in df["address"].values:
        df.loc[df["address"] == address, "reason"] = reason
    else:
        df = pd.concat([df, pd.DataFrame([{"address": address, "reason": reason}])], ignore_index=True)

    df.to_csv(ALPHA_CSV_PATH, index=False)
    await update.message.reply_text(f"✅ 已屏蔽地址：`{address}`\n原因：{reason}", parse_mode="Markdown")
