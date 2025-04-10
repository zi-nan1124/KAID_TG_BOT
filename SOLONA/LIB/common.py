# 标准库
import os
import sys
import json
import time
import asyncio
import random
import threading
import inspect
from math import ceil
from datetime import datetime,timedelta
from time import sleep
from typing import List, Dict
from concurrent.futures import ThreadPoolExecutor, as_completed
from multiprocessing import Pool, cpu_count
import traceback

# 第三方库
import requests
import pandas as pd
import httpx
from tqdm import tqdm
from colorama import Fore, Style

# Solana SDK
from solana.rpc.api import Client
from solana.rpc.core import RPCException
from solders.signature import Signature
from solders.pubkey import Pubkey

#logger
from SOLONA.LIB.Logger import Logger

# 添加根目录到 sys.path，确保可以导入 config.py
current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.abspath(os.path.join(current_dir, "../../"))
if root_dir not in sys.path:
    sys.path.append(root_dir)

import config

# 创建单例 logger
logger = Logger()

def print_trade_history_colored(df: pd.DataFrame):
    for _, row in df.iterrows():
        direction = row["方向"]
        color = Fore.GREEN if direction == "买入" else Fore.RED if direction == "卖出" else ""
        print(color + f"{row['时间']} | {direction} | Token: {row['Token']} | 数量: {row['数量']:.6f} | 价值(USD): {row['价值(USD)']:.2f}")
