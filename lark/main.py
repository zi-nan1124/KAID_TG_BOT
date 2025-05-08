"""
Main entry point for the lark_server framework.
This file initializes and runs the framework, integrating business logic and larkapi components.
"""

import time
import logging
from config import BlockTime_Fetcher_MESSAGE_PUSH_INTERVAL
from business_logic.BlockTime_Fetcher import BlockTime_Fetcher
from apscheduler.schedulers.background import BackgroundScheduler
import time
import logging

logger = logging.getLogger(__name__)

def fetch_job():
    try:
        logger.info("Running BlockTime_Fetcher...")
        fetcher = BlockTime_Fetcher()
        fetcher.run()  # 假设有 run_once 方法
    except Exception as e:
        logger.exception(f"BlockTime_Fetcher error: {e}")

def main():
    logger.info("Lark Server framework started.")

    scheduler = BackgroundScheduler()
    scheduler.add_job(fetch_job, 'interval', seconds=BlockTime_Fetcher_MESSAGE_PUSH_INTERVAL)  # 每 600 秒执行一次
    scheduler.start()

    try:
        while True:
            time.sleep(1)  # 保持主线程运行
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()

if __name__ == "__main__":
    main()
