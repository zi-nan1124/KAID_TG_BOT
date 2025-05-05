# === bot_server.py ===
import sys
import os
import logging
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler

# 设置项目根目录
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(PROJECT_ROOT)

# 导入配置和各 handler
import config
from handlers.start_handler import start
from handlers.profit_handler import profit
from handlers.decode_handler import decode
from handlers.toptrader_handler import findtoptrader
from handlers.alpha_handler import alpha_handler
from handlers.alpha_update_handler import alpha_mute, handle_mute_callback

def setup_logging():
    logging.basicConfig(
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        level=logging.INFO,
    )
    logging.getLogger("httpx").setLevel(logging.WARNING)  # 如果用 httpx，减少无关日志
    logging.getLogger("telegram").setLevel(logging.INFO)

def main():
    setup_logging()
    logger = logging.getLogger(__name__)

    logger.info("🚀 初始化 Telegram Bot 应用...")
    app = ApplicationBuilder().token(config.CONFIG["telegram_token"]).build()

    logger.info("✅ 注册指令处理器...")
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("profit", profit))
    app.add_handler(CommandHandler("decode", decode))
    app.add_handler(CommandHandler("findtoptrader", findtoptrader))
    app.add_handler(CommandHandler("alpha", alpha_handler))
    app.add_handler(CommandHandler("alpha_mute", alpha_mute))
    app.add_handler(CallbackQueryHandler(handle_mute_callback, pattern="^mute_"))

    logger.info("✅ 全部 handler 注册完成。")
    logger.info("✅ 开始轮询消息（Polling）...")

    print("\u2705 TG Bot 正在运行中...")
    app.run_polling()

if __name__ == "__main__":
    import pandas as pd
    #from utils import format_utils, safe_math  # 预留 utils 未来扩展

    pd.set_option("display.max_columns", None)
    pd.set_option("display.max_rows", None)
    pd.set_option("display.width", 200)
    pd.set_option("display.float_format", '{:.9f}'.format)

    main()
