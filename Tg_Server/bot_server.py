# === bot_server.py ===
import sys
import os
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(PROJECT_ROOT)
import config
from telegram.ext import ApplicationBuilder, CommandHandler
from telegram.ext import CallbackQueryHandler


from handlers.start_handler import start
from handlers.profit_handler import profit
from handlers.decode_handler import decode
from handlers.toptrader_handler import findtoptrader
from handlers.alpha_handler import alpha_handler
from handlers.alpha_update_handler import alpha_mute
from handlers.alpha_update_handler import handle_mute_callback






def main():
    app = ApplicationBuilder().token(config.CONFIG["telegram_token"]).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("profit", profit))
    app.add_handler(CommandHandler("decode", decode))
    app.add_handler(CommandHandler("findtoptrader", findtoptrader))
    app.add_handler(CommandHandler("alpha", alpha_handler))
    app.add_handler(CommandHandler("alpha_mute", alpha_mute))
    app.add_handler(CallbackQueryHandler(handle_mute_callback, pattern="^mute_"))

    print("\u2705 TG Bot \u6b63\u5728\u8fd0\u884c\u4e2d...")
    app.run_polling()

if __name__ == "__main__":
    import pandas as pd
    #from utils import format_utils, safe_math  # 加载 utils 模块（便于未来功能扩展）

    pd.set_option("display.max_columns", None)
    pd.set_option("display.max_rows", None)
    pd.set_option("display.width", 200)
    pd.set_option("display.float_format", '{:.9f}'.format)
    main()
