from birdeye.lib.common import *

class BirdeyeTokenFetcher:
    def __init__(self):
        self.max_pages = 5
        self.base_url = "https://public-api.birdeye.so/defi/tokenlist"

    def human_format(self, num):
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

    def fetch(self, chain):
        logger.info(f"📡 开始抓取 {chain.upper()} Token 数据...")
        params = {
            "sort_by": "liquidity",
            "sort_type": "desc",
            "offset": 0,
            "limit": 50,
            "min_liquidity": 100,
            "max_liquidity": 100_000_000_000
        }
        headers = {
            "accept": "application/json",
            "x-chain": chain,
            "X-API-KEY": config.CONFIG["BIRDEYE_APIKEY"]
        }

        all_tokens = []

        for page in range(self.max_pages):
            logger.info(f"🔄 正在请求第 {page+1} 页（max_liquidity = {params['max_liquidity']}）")
            try:
                response = requests.get(self.base_url, headers=headers, params=params, timeout=10)
            except Exception as e:
                logger.error(f"请求异常：{str(e)}")
                break

            if response.status_code != 200:
                logger.error(f"请求失败：{response.status_code} - {response.text}")
                break

            batch = response.json().get("data", {}).get("tokens", [])
            if not batch:
                logger.info("✅ 没有更多数据，提前结束")
                break

            all_tokens.extend(batch)
            min_liquidity = min([t.get("liquidity", 0) for t in batch])
            if min_liquidity <= 100:
                break
            params["max_liquidity"] = min_liquidity - 1
            time.sleep(0.5)

        logger.info(f"📦 共获取 {len(all_tokens)} 条记录，正在去重和排序...")

        unique = {t["address"]: t for t in all_tokens}
        sorted_tokens = sorted(unique.values(), key=lambda x: x.get("v24hUSD", 0), reverse=True)

        rows = [{
            "代币符号": t.get("symbol", ""),
            "代币地址": t.get("address", ""),
            "24小时交易量": self.human_format(t.get("v24hUSD", 0)),
            "流动性": self.human_format(t.get("liquidity", 0)),
            "价格": f"${t.get('price', 0):,.4f}"
        } for t in sorted_tokens]

        logger.info(f"✅ 去重后共 {len(rows)} 条记录")
        return pd.DataFrame(rows)


if __name__ == "__main__":
    fetcher = BirdeyeTokenFetcher()
    df = fetcher.fetch("bsc")
    df.to_csv("test.csv", index=False, encoding="utf-8-sig")
