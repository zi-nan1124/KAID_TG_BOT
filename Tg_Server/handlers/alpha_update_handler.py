# Tg_Server/handlers/alpha_update_handler.py
import os
import pandas as pd
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

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


async def handle_mute_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data  # 例子："mute_0x123456789ABCDEF_SYMBOL"
    parts = data.split("_", 2)

    if len(parts) < 3:
        await query.answer(text="❌ 回调数据格式错误", show_alert=True)
        return

    _, address, reason = parts

    ALPHA_CSV_PATH = os.path.join(CONFIG["tg_server_data_path"], "alpha.csv")

    if not os.path.exists(ALPHA_CSV_PATH):
        df = pd.DataFrame(columns=["address", "reason"])
        df.to_csv(ALPHA_CSV_PATH, index=False)

    df = pd.read_csv(ALPHA_CSV_PATH)

    if address in df["address"].values:
        df.loc[df["address"] == address, "reason"] = reason
    else:
        df = pd.concat([df, pd.DataFrame([{"address": address, "reason": reason}])], ignore_index=True)

    df.to_csv(ALPHA_CSV_PATH, index=False)

    # 🔥 重点处理：更新按钮
    old_markup = query.message.reply_markup
    new_buttons = []

    for row in old_markup.inline_keyboard:
        button = row[0]  # 每行只有一个按钮
        # 匹配当前按钮是否是被Mute的
        if button.callback_data == data:
            # 替换成 Muted✅
            new_button = InlineKeyboardButton(
                text=f"Muted ✅ {reason}",
                callback_data=button.callback_data  # 这里保持callback_data不变（方便多次处理）
            )
            new_buttons.append([new_button])
        else:
            # 保持其他按钮不动
            new_buttons.append(row)

    new_markup = InlineKeyboardMarkup(new_buttons)

    # 编辑按钮
    await query.edit_message_reply_markup(reply_markup=new_markup)

    # （选填）额外弹气泡
    await query.answer(text=f"✅ 已屏蔽 {reason}", show_alert=False)
