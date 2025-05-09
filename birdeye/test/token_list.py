import requests
import pandas as pd

def human_format(num):
    if num >= 1e9:
        return f"{num/1e9:.2f}B"
    elif num >= 1e6:
        return f"{num/1e6:.2f}M"
    elif num >= 1e3:
        return f"{num/1e3:.2f}K"
    else:
        return f"{num:.2f}"

pd.set_option('display.max_columns', None)
pd.set_option("display.width", 200)

url = "https://public-api.birdeye.so/defi/tokenlist?sort_by=v24hUSD&sort_type=desc&offset=0&limit=50&min_liquidity=100"
headers = {
    "accept": "application/json",
    "x-chain": "bsc",
    "X-API-KEY": "b00c15043820435084c08a8dc16aa14f"
}

response = requests.get(url, headers=headers)

if response.status_code == 200:
    tokens = response.json()["data"]["tokens"]

    rows = []
    for token in tokens:
        rows.append({
            "symbol": token.get("symbol", ""),
            "mintAddress": token.get("address", ""),  # ✅ 保留完整地址
            "v24hUSD": human_format(token.get("v24hUSD", 0)),
            "liquidity": human_format(token.get("liquidity", 0)),
            "price": f"${token.get('price', 0):,.4f}"
        })

    df = pd.DataFrame(rows, columns=["symbol", "mintAddress", "v24hUSD", "liquidity", "price"])
    print("📊 可视化 Top Token DataFrame（含完整地址）：\n")
    print(df.head(50))
    df.to_csv(f"{headers['x-chain']}.csv", index=False, encoding='utf-8-sig')


else:
    print("❌ Error:", response.status_code)
    print(response.text)
