import requests
import pandas as pd
import time

# 👇 在这里填入你的钱包地址列表
wallets = [
    "71CPXu3TvH3iUKaY1bNkAAow24k6tjH473SsKprQBABC",
    "ErANnmZypLGTGibGESSDX5V2aqh7CYepHmTB26VimYDQ",
    # 可继续添加...
]

# 通用参数（从你的抓包中得出，GMGN 没有签名机制）
params = {
    "device_id": "23b2fd66-34e8-41dd-bf90-5870d63fd6be",
    "client_id": "gmgn_web_2025.0414.203636",
    "from_app": "gmgn",
    "app_ver": "2025.0414.203636",
    "tz_name": "Asia/Singapore",
    "tz_offset": "28800",
    "app_lang": "zh-CN",
    "fp_did": "7ac271ff106baa3a90693e72a0ddd108",
    "os": "web",
    "period": "7d"
}

# 标准浏览器请求头
headers = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Encoding": "gzip, deflate, br",
    "Accept-Language": "zh-CN,zh;q=0.9",
}

def fetch_wallet_stat(address):
    url = f"https://www.gmgn.ai/api/v1/wallet_stat/sol/{address}/7d"
    headers["Referer"] = f"https://www.gmgn.ai/sol/address/{address}"
    try:
        resp = requests.get(url, headers=headers, params=params, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            print(f"✅ 成功获取 {address}")
            return {
                "address": address,
                "data": data
            }
        else:
            print(f"❌ 请求失败 {address} - 状态码: {resp.status_code}")
            return {
                "address": address,
                "data": None
            }
    except Exception as e:
        print(f"❌ 请求错误 {address} - {e}")
        return {
            "address": address,
            "data": None
        }

# 运行主流程
results = []
for addr in wallets:
    result = fetch_wallet_stat(addr)
    results.append(result)
    time.sleep(0.6)  # 防止过快触发限流

# 展平嵌套结构，提取关键字段（示例字段，请根据实际返回数据结构调整）
def flatten_result(entry):
    flat = {
        "address": entry["address"]
    }
    data = entry["data"]
    if data:
        for k, v in data.items():
            flat[k] = v
    return flat

# 生成 DataFrame
flat_results = [flatten_result(r) for r in results if r["data"]]
df = pd.DataFrame(flat_results)

# 导出为 CSV
df.to_csv("gmgn_wallet_data.csv", index=False)
print("📁 已保存为 gmgn_wallet_data.csv")
