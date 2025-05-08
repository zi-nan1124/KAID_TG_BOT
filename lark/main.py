"""
Main entry point for the lark_server framework.
This file initializes and runs the framework, integrating business logic and larkapi components.
"""

import time
import logging
from config import APP_ID, APP_SECRET, USERID, MESSAGE_PUSH_INTERVAL
from larkapi.message_sender import LarkMessageSender
from business_logic.BNfetcher import BNfetcher
from apscheduler.schedulers.background import BackgroundScheduler
import time
import logging

logger = logging.getLogger(__name__)

def fetch_job():
    try:
        logger.info("Running BNfetcher...")
        fetcher = BNfetcher()
        fetcher.run()  # 假设有 run_once 方法
    except Exception as e:
        logger.exception(f"BNfetcher error: {e}")

def main():
    logger.info("Lark Server framework started.")
    sender = LarkMessageSender(APP_ID, APP_SECRET)

    scheduler = BackgroundScheduler()
    scheduler.add_job(fetch_job, 'interval', seconds=MESSAGE_PUSH_INTERVAL)  # 每 600 秒执行一次
    scheduler.start()

    try:
        while True:
            time.sleep(1)  # 保持主线程运行
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()

if __name__ == "__main__":
    main()
