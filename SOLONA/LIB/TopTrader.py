from SOLONA.LIB.common import *
from SOLONA.LIB.Sol_Wallet_Fetcher import SolanaWalletExplorer


class TopTraderFinder:
    def __init__(self, api_key: str, max_trade_count: int = 20000):
        self.api_key = api_key
        self.max_trade_count = max_trade_count
        self.base_url = "https://public-api.birdeye.so/defi/v2/tokens/top_traders"
        self.headers = {
            "accept": "application/json",
            "x-chain": "solana",
            "X-API-KEY": self.api_key
        }

    def get_wallets(self, token_address: str, time_frame: str = "24h", limit: int = 10, offset: int = 0) -> pd.DataFrame:
        params = {
            "address": token_address,
            "time_frame": time_frame,
            "sort_type": "desc",
            "sort_by": "volume",
            "offset": offset,
            "limit": limit
        }
        response = requests.get(self.base_url, headers=self.headers, params=params)
        if response.status_code == 200:
            items = response.json().get("data", {}).get("items", [])
            data = [{"walletaddress": item["owner"], "trade_count": item["trade"]} for item in items]
            return pd.DataFrame(data)
        else:
            print(f"请求失败: {response.status_code}")
            return pd.DataFrame(columns=["walletaddress", "trade_count"])

    def batch_calculate_profit_summary(self, wallet_df: pd.DataFrame) -> pd.DataFrame:
        """
        多线程并发分析7日盈利，返回一个 DataFrame：
        - 每个钱包都有记录；失败的为 NaN，但保留 wallet 字段
        """
        rpc_url = config.CONFIG["rpc_url"]
        summary_list = []

        def analyze_wallet(wallet_address):
            try:
                explorer = SolanaWalletExplorer(
                    rpc_url=rpc_url,
                    wallet_address=wallet_address
                )
                _, summary = explorer.calculate_profit_by_7_day()
                if summary is None:
                    return {"wallet": wallet_address}
                else:
                    summary["wallet"] = wallet_address
                    return summary
            except Exception as e:
                print(f"[ERROR] 钱包 {wallet_address} 异常：{e}")
                return {"wallet": wallet_address}

        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = {
                executor.submit(analyze_wallet, row["walletaddress"]): row["walletaddress"]
                for _, row in wallet_df.iterrows()
            }

            for future in tqdm(as_completed(futures), total=len(futures), desc="Calculating profits"):
                result = future.result()
                summary_list.append(result)

        summary_df = pd.DataFrame(summary_list)
        return summary_df


# 示例调用
if __name__ == "__main__":
    pd.set_option("display.max_columns", None)
    pd.set_option("display.max_rows", None)
    pd.set_option("display.width", 200)
    pd.set_option("display.float_format", '{:.9f}'.format)

    API_KEY = "1417024180f241ac91e88350dc2a1058"
    TOKEN_ADDRESS = "C3DwDjT17gDvvCYC2nsdGHxDHVmQRdhKfpAdqQ29pump"

    finder = TopTraderFinder(api_key=API_KEY, max_trade_count=50)

    df = finder.get_wallets(token_address=TOKEN_ADDRESS)
    print(f"\n获取到 {len(df)} 个地址，准备分析")

    summary_df = finder.batch_calculate_profit_summary(df)

    print("\n✅ 分析完成的 summary_df：")
    print(summary_df)
