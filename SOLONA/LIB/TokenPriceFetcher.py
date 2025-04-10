from SOLONA.LIB.common import *



class TokenPriceFetcher:
    def __init__(self):
        self.api_key = config.CONFIG["BIRDEYE_APIKEY"]
        self.base_url = "https://public-api.birdeye.so/defi/multi_price"
        self.headers = {
            "accept": "application/json",
            "x-chain": "solana",
            "X-API-KEY": self.api_key
        }
        self.batch_size = 100

    def fetch_prices(self, address_df: pd.DataFrame) -> pd.DataFrame:
        if 'address' not in address_df.columns:
            raise ValueError("DataFrame 缺少 'address' 列")

        all_addresses = (
            address_df['address']
            .dropna()
            .unique()
            .tolist()
        )

        # ✅ 过滤掉 "UNKNOWN" 和空字符串
        all_addresses = [addr for addr in all_addresses if addr != "UNKNOWN" and addr.strip() != ""]

        logger.info(f"开始获取价格，共 {len(all_addresses)} 个地址")

        all_results = []
        for i in range(0, len(all_addresses), self.batch_size):
            batch = all_addresses[i:i + self.batch_size]
            logger.info(f"正在处理第 {(i // self.batch_size) + 1} 批（{len(batch)} 个地址）")
            try:
                batch_result = self._fetch_batch(batch)
                all_results.extend(batch_result)
            except Exception as e:
                logger.error(f"第 {(i // self.batch_size) + 1} 批失败：{str(e)}")
            sleep(0.2)

        logger.info(f"价格获取完成，成功获取 {len(all_results)} 条记录")
        return pd.DataFrame(all_results)

    def _fetch_batch(self, address_list: List[str]) -> List[dict]:
        joined = ','.join(address_list)
        url = f"{self.base_url}?include_liquidity=false&list_address={joined}"
        response = requests.get(url, headers=self.headers)
        if response.status_code != 200:
            raise Exception(f"BirdEye API 请求失败：{response.status_code} - {response.text}")

        data = response.json().get("data", {})
        result = []
        for addr in address_list:
            price = data.get(addr, {}).get("value")
            result.append({"address": addr, "price": price})
        return result

    def fetch_SOL_price(self) -> float:
        """获取当前 SOL 价格（float），失败返回 None"""
        sol_address = "So11111111111111111111111111111111111111112"
        url = f"{self.base_url}?include_liquidity=false&list_address={sol_address}"

        try:
            response = requests.get(url, headers=self.headers)
            if response.status_code != 200:
                raise Exception(f"API 状态码错误：{response.status_code} - {response.text}")

            data = response.json().get("data", {})
            price = data.get(sol_address, {}).get("value")

            if price is None:
                logger.warn("SOL 价格返回为空")
                return None

            return float(price)
        except Exception as e:
            logger.error(f"获取 SOL 价格失败：{str(e)}")
            return None

    def fetch_wallet_token_list(self, wallet_address: str) -> pd.DataFrame:
        """根据钱包地址获取其持有的 token 列表（含地址和余额）"""
        url = f"https://public-api.birdeye.so/v1/wallet/token_list?wallet={wallet_address}"
        try:
            response = requests.get(url, headers=self.headers)
            if response.status_code != 200:
                raise Exception(f"API 请求失败：{response.status_code} - {response.text}")

            raw_data = response.json()
            if not raw_data.get("success"):
                raise Exception("BirdEye API 返回失败状态")

            items = raw_data["data"].get("items", [])
            result = []
            for token in items:
                token_address = token.get("address")
                token_balance = token.get("uiAmount")  # 已按 decimal 转换
                result.append({
                    "token_address": token_address,
                    "token_balance": token_balance
                })

            logger.info(f"钱包 {wallet_address} 持有 {len(result)} 个 Token")
            return pd.DataFrame(result)

        except Exception as e:
            logger.error(f"获取钱包 Token 列表失败：{str(e)}")
            return pd.DataFrame(columns=["token_address", "token_balance"])




if __name__ == "__main__":
    # 示例地址列表（可扩展模拟分页）
    pd.options.display.float_format = '{:.12f}'.format

    sample_addresses = [
        "So11111111111111111111111111111111111111112",
        "DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263"
    ]
    sample_addresses *= 60  # 共 120 地址

    df = pd.DataFrame({"address": sample_addresses})

    fetcher = TokenPriceFetcher()
    try:
        result_df = fetcher.fetch_prices(df)
        print(result_df)
    except Exception as e:
        logger.error(f"发生错误：{str(e)}")


    # 获取 SOL 价格测试
    sol_price = fetcher.fetch_SOL_price()
    if sol_price is not None:
        logger.info(f"当前 SOL 价格为: {sol_price:.4f} USD")
    else:
        logger.warn("未能成功获取 SOL 价格")

    # 钱包 token 列表测试
    wallet_address = "DW1DdpQ9JGY4up2yRSg8gKeH9ZwG9xXvywgA6GfWo99a"
    token_df = fetcher.fetch_wallet_token_list(wallet_address)
    logger.info(f"钱包 {wallet_address} 持仓预览：\n{token_df.head().to_string(index=False)}")


