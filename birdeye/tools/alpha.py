import pandas as pd
import requests
import time

# === 参数配置 ===
CSV_PATH = "old.xlsx"  # 你的 Excel 文件名
API_KEY = "e1d725690a9c42979d389412f06fa852"
BIRDEYE_API = "https://public-api.birdeye.so/defi/v3/token/market-data"
MARKETCAP_THRESHOLD = 1_000_000

CHAIN_MAPPING = {
    "SOL": "solana",
    "BSC": "bsc",
    "BASE": "base"
}

# === 第一步：读取 Excel 并筛选 ===
df = pd.read_excel(CSV_PATH)
if pd.api.types.is_numeric_dtype(df["登记时间"]):
    df["登记时间"] = pd.to_datetime(df["登记时间"], unit='D', origin='1899-12-30')

# 只筛选在架 + 链是 SOL/BSC/BASE 的
filtered_df = df[(df["状态"] == "在架") & (df["链"].isin(["SOL", "BSC", "BASE"]))]

if filtered_df.empty:
    print("没有符合条件的在架 SOL/BSC/BASE 链 token")
    exit()

# === 第二步：分链处理，每个链分别请求 ===
results = []
not_qualified_tokens = []  # 存储不合格的token名字

for chain_key, group_df in filtered_df.groupby("链"):
    chain_name = CHAIN_MAPPING.get(chain_key)
    if not chain_name:
        print(f"⚠️ 未知链 {chain_key}，跳过")
        continue

    addresses = group_df["合约地址"].tolist()

    for idx, addr in enumerate(addresses, 1):
        url = f"{BIRDEYE_API}?address={addr}"
        headers = {
            "accept": "application/json",
            "x-chain": chain_name,
            "X-API-KEY": API_KEY,
            "User-Agent": "Mozilla/5.0"
        }

        response = requests.get(url, headers=headers)

        if response.status_code == 401:
            print("❌ 401 错误：API KEY 无效或者请求头错误，请检查 API KEY 是否正确、Header 是否规范！")
            exit()

        if response.status_code != 200:
            print(f"❗ 请求失败：链 {chain_key} 地址 {addr}，状态码 {response.status_code}")
            continue

        data = response.json().get("data", {})

        price = data.get("price")
        market_cap = data.get("market_cap", 0)
        liquidity = data.get("liquidity")

        # 打印每个 token 的关键信息
        print(f"[{chain_key}] [{idx}/{len(addresses)}] 地址: {addr} | 价格: {price} | 市值: {market_cap} | 流动性: {liquidity}")

        token_row = group_df[group_df["合约地址"] == addr].iloc[0].to_dict()

        if market_cap is not None and market_cap < MARKETCAP_THRESHOLD:
            token_row.update({
                "市场价": price,
                "市值": market_cap,
                "流动性": liquidity
            })
            results.append(token_row)
        else:
            token_name = str(token_row["币种"]) if pd.notna(token_row["币种"]) else ""
            not_qualified_tokens.append(token_name)

        time.sleep(0.01)  # 防止请求太快被限速

# === 第三步：保存符合条件的结果 ===
if results:
    result_df = pd.DataFrame(results)

    # 只保留指定列
    columns_to_keep = [
        "登记时间", "币种", "状态", "链", "合约地址", "值班员", "市值"
    ]
    result_df = result_df[columns_to_keep]

    result_df.to_csv("filtered_tokens.csv", index=False, encoding="utf-8-sig")
    print("✅ 已保存市值小于 1M 的 Token 到 filtered_tokens.csv（已去除市场价和流动性列）")
else:
    print("⚠️ 没有符合市值条件的 token")

# === 第四步：打印不合格token名字 ===
if not_qualified_tokens:
    tokens_line = ",".join(not_qualified_tokens)
    print(f"❗ 不符合市值条件的币种有：{tokens_line}")
