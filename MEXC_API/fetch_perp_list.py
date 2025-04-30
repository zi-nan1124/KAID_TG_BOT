import requests
import pandas as pd

def fetch_mexc_dex_tokens(chain_id="56", max_page=10):
    all_tokens = set()

    for page in range(1, max_page + 1):
        url = "https://www.mexc.com/api/platform/spot/market/queryPairs"
        headers = {"Content-Type": "application/json"}
        payload = {
            "chainId": str(chain_id),
            "pageSize": 100,
            "pageNum": page
        }

        try:
            response = requests.post(url, json=payload, headers=headers, timeout=10)
            response.raise_for_status()
            data = response.json()
        except Exception as e:
            print(f"[请求失败] 第 {page} 页出错: {e}")
            break

        pairs = data.get("data", {}).get("records", [])
        if not pairs:
            print(f"[INFO] 第 {page} 页没有更多 pairs，提前结束")
            break

        for pair in pairs:
            all_tokens.add(pair["baseToken"]["symbol"].lower())
            all_tokens.add(pair["quoteToken"]["symbol"].lower())

    return list(all_tokens)

def main():
    tokens = fetch_mexc_dex_tokens()
    if not tokens:
        print("[终止] 没有拿到 token 列表")
        return

    print(f"✅ 获取到 {len(tokens)} 个独立代币")
    df = pd.DataFrame(tokens, columns=["token"])
    df.to_csv("mexc_dex_tokens.csv", index=False)
    print("✅ 已保存到 mexc_dex_tokens.csv")

if __name__ == "__main__":
    main()
