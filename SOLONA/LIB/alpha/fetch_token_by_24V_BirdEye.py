import requests
import pandas as pd
from SOLONA.LIB.common import *

class BirdEyeFetcher:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://public-api.birdeye.so/defi/tokenlist"
        self.headers = {
            "accept": "application/json",
            "X-API-KEY": self.api_key
        }

    def fetch_chain_tokens(self, chain: str) -> pd.DataFrame:
        params = {
            "sort_by": "v24hUSD",
            "sort_type": "desc",
            "offset": 0,
            "limit": 50,
            "min_liquidity": 100
        }
        headers = self.headers.copy()
        headers["x-chain"] = chain

        response = requests.get(self.base_url, headers=headers, params=params)
        response.raise_for_status()
        data = response.json()

        tokens = data.get("data", {}).get("tokens", [])
        df = pd.DataFrame(tokens)
        if df.empty:
            return pd.DataFrame(columns=["symbol", "address", "chain", "v24hUSD", "mc"])

        df = df[["symbol", "address", "v24hUSD", "mc"]]
        df = df[df["mc"] >= 1_000_000]
        df["chain"] = chain
        df = df[["symbol", "address", "chain", "v24hUSD", "mc"]]
        return df

    def fetch_all(self, chains=("solana", "bsc")) -> pd.DataFrame:
        all_dfs = []
        for chain in chains:
            try:
                df = self.fetch_chain_tokens(chain)
                all_dfs.append(df)
            except Exception as e:
                print(f"⚠️ Error fetching {chain}: {e}")
        return pd.concat(all_dfs, ignore_index=True)


if __name__ == "__main__":

    fetcher = BirdEyeFetcher(api_key=config.CONFIG["BIRDEYE_APIKEY"])
    df = fetcher.fetch_all()
    pd.set_option("display.max_columns", None)
    pd.set_option("display.max_rows", None)  # 显示所有行
    pd.set_option("display.width", 200)
    pd.set_option("display.float_format", '{:.9f}'.format)
    print(df)
