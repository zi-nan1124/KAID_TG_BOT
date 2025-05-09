import requests
import pandas as pd
import json
from datetime import datetime
import time

def to_timestamp(timestr: str) -> int:
    """将可读时间字符串转换为 Unix 时间戳"""
    dt = datetime.strptime(timestr, "%Y-%m-%d %H:%M:%S")
    return int(time.mktime(dt.timetuple()))

def fetch_birdeye_price_history(
    address: str,
    time_from_str: str,
    time_to_str: str,
    time_type: str,
    address_type: str = "token",
    api_key: str = "1417024180f241ac91e88350dc2a1058",
    output_csv: str = "price_history.csv"
):
    time_from = to_timestamp(time_from_str)
    time_to = to_timestamp(time_to_str)

    url = (
        f"https://public-api.birdeye.so/defi/history_price"
        f"?address={address}"
        f"&address_type={address_type}"
        f"&type={time_type}"
        f"&time_from={time_from}"
        f"&time_to={time_to}"
    )

    headers = {
        "accept": "application/json",
        "x-chain": "solana",
        "X-API-KEY": api_key
    }

    response = requests.get(url, headers=headers)

    try:
        data = response.json()
    except json.JSONDecodeError:
        print("❌ 返回内容不是合法的 JSON：")
        print(response.text)
        return None

    # 打印 JSON 响应
    print(json.dumps(data, indent=2))

    # 写入 CSV
    if data.get("success") and "items" in data.get("data", {}):
        df = pd.DataFrame(data["data"]["items"])
        df["datetime"] = df["unixTime"].apply(lambda ts: datetime.utcfromtimestamp(ts).isoformat())
        df.to_csv(output_csv, index=False)
        print(f"✅ 数据已保存到 {output_csv}")
        return df
    else:
        print("⚠️ 返回数据格式不正确或 success=false")
        return None


# 示例调用
if __name__ == "__main__":
    fetch_birdeye_price_history(
        address="So11111111111111111111111111111111111111112",
        time_from_str="2024-05-01 00:00:00",
        time_to_str="2024-05-01 00:00:00",
        time_type = "1m"
    )
