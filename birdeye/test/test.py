import requests
import pandas as pd
import time  # 用于时间戳处理

url = "https://public-api.birdeye.so/defi/v3/token/list"
headers = {
    "accept": "application/json",
    "x-chain": "bsc",  # or "bsc"
    "X-API-KEY": "1417024180f241ac91e88350dc2a1058"
}

# 当前时间 - 24 小时（单位：秒）
now = int(time.time())
unix_24h_ago = now - 86400

params = {
    "sort_by": "volume_24h_usd",
    "sort_type": "desc",
    "min_liquidity": 10,
    "max_liquidity": 10000000,
    "min_market_cap": 10,
    "max_market_cap": 10000000,
    "min_fdv": 10,
    "max_fdv": 10000000,

}

response = requests.get(url, headers=headers, params=params)
data = response.json().get("data", {}).get("items", [])

if not data:
    print("❌ 无数据返回")
    exit()

rows = []
for item in data:
    rows.append({
        "symbol": item.get("symbol"),
        "name": item.get("name"),
        "price": item.get("price"),
        "volume_24h": item.get("volume_24h_usd"),
        "liquidity": item.get("liquidity"),
        "market_cap": item.get("market_cap"),
        "fdv": item.get("fdv"),
        "holders": item.get("holder"),
        "trade_24h_count": item.get("trade_24h_count"),
        "price_change_24h_percent": item.get("price_change_24h_percent"),
        "volume_24h_change_percent": item.get("volume_24h_change_percent"),
        "last_trade_time": item.get("last_trade_unix_time")
    })

df = pd.DataFrame(rows)
print(df.head(10))
