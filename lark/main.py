"""
Main entry point for the lark_server framework.
This file initializes and runs the framework, integrating business logic and larkapi components.
"""

import time
import logging
from lark.config import APP_ID, APP_SECRET, USERID, MESSAGE_PUSH_INTERVAL
from larkapi.message_sender import LarkMessageSender
from business_logic.BNfetcher import BNfetcher

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    logger.info("Lark Server framework started.")
    sender = LarkMessageSender(APP_ID, APP_SECRET)
    BN_fetcher = BNfetcher()
    BN_fetcher.run_forever()

if __name__ == "__main__":
    main()
