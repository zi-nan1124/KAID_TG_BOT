import requests
import pandas as pd
import time

def human_format(num):
    if num is None:
        return "-"
    elif num >= 1e9:
        return f"{num/1e9:.2f}B"
    elif num >= 1e6:
        return f"{num/1e6:.2f}M"
    elif num >= 1e3:
        return f"{num/1e3:.2f}K"
    else:
        return f"{num:.2f}"

pd.set_option('display.max_columns', None)
pd.set_option("display.width", 200)

headers = {
    "accept": "application/json",
    "x-chain": "bsc",  # or "bsc"
    "X-API-KEY": "1417024180f241ac91e88350dc2a1058"
}

base_url = "https://public-api.birdeye.so/defi/tokenlist"
params = {
    "sort_by": "liquidity",
    "sort_type": "desc",
    "offset": 0,
    "limit": 50,
    "min_liquidity": 100,
    "max_liquidity": 100_000_000_000  # 初始最大流动性设置为100B
}

all_tokens = []
max_rounds = 10

for i in range(max_rounds):
    print(f"📦 正在获取第 {i+1} 批数据 (max_liquidity = {params['max_liquidity']})")
    response = requests.get(base_url, headers=headers, params=params)

    if response.status_code != 200:
        print("❌ 请求失败:", response.status_code, response.text)
        break

    batch = response.json()["data"]["tokens"]
    if not batch:
        print("✅ 没有更多数据，提前结束。")
        break

    all_tokens.extend(batch)

    # 更新 max_liquidity 为本轮最小值 - 1，避免重复
    min_liquidity = min([t.get("liquidity", 0) for t in batch])
    if min_liquidity <= 100:
        break
    params["max_liquidity"] = min_liquidity - 1

    time.sleep(0.5)  # 为避免频率限制，加个间隔

# 🔄 合并并去重（按 address 去重）
unique = {}
for token in all_tokens:
    unique[token["address"]] = token
tokens = list(unique.values())

# ✅ 按 24h 交易量降序排列
tokens = sorted(tokens, key=lambda x: x.get("v24hUSD", 0), reverse=True)

# 🔧 转换为 DataFrame 并格式化
rows = []
for token in tokens:
    rows.append({
        "代币符号": token.get("symbol", ""),
        "代币地址": token.get("address", ""),
        "24小时交易量": human_format(token.get("v24hUSD", 0)),
        "流动性": human_format(token.get("liquidity", 0)),
        "价格": f"${token.get('price', 0):,.4f}"
    })

df = pd.DataFrame(rows, columns=["代币符号", "代币地址", "24小时交易量", "流动性", "价格"])
print("📊 按 24h 交易量排序后结果：\n")
print(df.head(50))

# ✅ 保存 CSV 文件
file_name = f"{headers['x-chain']}.csv"
df.to_csv(file_name, index=False, encoding='utf-8-sig')
print(f"✅ 已保存为 CSV 文件：{file_name}")
