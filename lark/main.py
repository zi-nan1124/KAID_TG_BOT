"""
Main entry point for the lark_server framework.
This file initializes and runs the framework, integrating business logic and larkapi components.
"""

import time
import logging
from config import APP_ID, APP_SECRET, USERID, MESSAGE_PUSH_INTERVAL
from larkapi.message_sender import LarkMessageSender

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    logger.info("Lark Server framework started.")
    sender = LarkMessageSender(APP_ID, APP_SECRET)

    while True:
        for user_id in USERID:
            success = sender.send_message(user_id, "test")
            if success:
                logger.info(f"Sent test message to {user_id}")
            else:
                logger.error(f"Failed to send test message to {user_id}")
        time.sleep(MESSAGE_PUSH_INTERVAL)

if __name__ == "__main__":
    main()
