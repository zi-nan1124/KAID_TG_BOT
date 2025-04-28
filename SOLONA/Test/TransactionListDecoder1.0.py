from SOLONA.LIB.common import *
from SOLONA.LIB.HeliusLogDecoder import HeliusLogDecoder
from SOLONA.LIB.PumpFunTradeDecoder import PumpFunTradeDecoder


def decode_single(tx_json):
    decoder = PumpFunTradeDecoder()
    try:
        df = decoder.decode(tx_json)
        if df is not None and not df.empty:
            return df
    except Exception as e:
        Logger().error(f"解析交易失败: {e}")
    return None


class TransactionListDecoder:
    def __init__(self):
        self.helius = HeliusLogDecoder()
        self.pump_decoder = PumpFunTradeDecoder()

        # 构建加权 RPC URL 池（付费节点权重为4）
        self.rpc_urls = [
            config.CONFIG["rpc_url"] * 4,
            config.CONFIG["rpc_url1"],
            config.CONFIG["rpc_url2"],
            config.CONFIG["rpc_url3"]
        ]
        self.rpc_pool = [config.CONFIG["rpc_url"]] * 4 + [
            config.CONFIG["rpc_url1"],
            config.CONFIG["rpc_url2"],
            config.CONFIG["rpc_url3"]
        ]

        self.client = Client(config.CONFIG["rpc_url"])
        self.http_client = httpx.AsyncClient(http2=True, timeout=30.0)

    def __del__(self):
        if self.http_client:
            try:
                asyncio.get_event_loop().run_until_complete(self.http_client.aclose())
            except:
                pass

    def parse_signatures(self, sig_df: pd.DataFrame):
        logger.info("开始解析签名...")
        signatures = sig_df["signature"].tolist()
        transactions = self.helius.batch_parse_transactions(signatures)

        result_all = [self.helius.summarize(tx) for tx in transactions if tx]
        df_all = pd.DataFrame(result_all)

        df_pump = df_all[df_all["protocol"].isin(["PUMP_FUN", "PUMP_AMM"])].copy()
        df_others = df_all[~df_all["protocol"].isin(["PUMP_FUN", "PUMP_AMM"])].copy()

        logger.info(f"共解析交易 {len(df_all)} 条，其中 PUMP 类型 {len(df_pump)} 条，其它类型 {len(df_others)} 条")
        return df_others, df_pump

    def _get_weighted_rpc_url(self):
        return random.choice(self.rpc_pool)

    async def fetch_one_tx(self, sig: str, max_retries=5, delay=1):
        for attempt in range(1, max_retries + 1):
            rpc_url = self._get_weighted_rpc_url()
            try:
                payload = {
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "getTransaction",
                    "params": [sig, {"maxSupportedTransactionVersion": 0}]
                }
                response = await self.http_client.post(rpc_url, json=payload)
                if response.status_code == 200:
                    res_json = response.json()
                    if res_json.get("result"):
                        logger.info(f"成功获取交易 {sig} via {rpc_url}")
                        return res_json["result"]
                    else:
                        logger.warn(f"交易 {sig} 第 {attempt} 次失败: 无结果返回")
                else:
                    logger.warn(f"交易 {sig} 第 {attempt} 次失败: 状态码 {response.status_code}")
            except Exception as e:
                logger.error(f"交易 {sig} 第 {attempt} 次异常: {e}")
            await asyncio.sleep(delay * attempt)
        logger.error(f"交易 {sig} 多次重试后失败")
        return None

    async def async_fetch_pump_tx_json(self, pump_df: pd.DataFrame) -> list:
        logger.info("开始异步获取 PUMP 交易 JSON 数据（加权 RPC 调度）...")
        pump_sigs = pump_df["signature"].tolist()
        tasks = [self.fetch_one_tx(sig) for sig in pump_sigs]
        results = await asyncio.gather(*tasks)
        return [r for r in results if r]

    def fetch_pump_tx_json(self, pump_df: pd.DataFrame) -> list:
        return asyncio.run(self.async_fetch_pump_tx_json(pump_df))

    def decode_pump_multithreaded(self, tx_json_list: list) -> pd.DataFrame:
        logger.info("开始多进程解析 PUMP 交易...")
        with Pool(processes=min(cpu_count(), 8)) as pool:
            results = pool.map(decode_single, tx_json_list)

        results = [df for df in results if df is not None]
        if results:
            final_df = pd.concat(results, ignore_index=True)
            logger.info(f"成功解析 {len(final_df)} 条 PUMP 交易")
            return final_df
        else:
            logger.warn("未解析出任何 PUMP 交易")
            return pd.DataFrame()

    def merge_results(self, df_others: pd.DataFrame, df_pump: pd.DataFrame) -> pd.DataFrame:
        logger.info("开始合并结果...")
        df_all = pd.concat([df_others, df_pump], ignore_index=True)
        if "timestamp" in df_all.columns:
            df_all = df_all.sort_values(by="timestamp", ascending=True)
        else:
            logger.warn("结果中缺少 timestamp 字段，无法排序")
        return df_all.reset_index(drop=True)

    def decode(self, sig_df: pd.DataFrame) -> pd.DataFrame:
        logger.info("开始全流程解析...")
        df_others, df_pump_init = self.parse_signatures(sig_df)
        tx_jsons = self.fetch_pump_tx_json(df_pump_init)
        df_pump_decoded = self.decode_pump_multithreaded(tx_jsons)
        df_all = self.merge_results(df_others, df_pump_decoded)
        logger.info(f"全部解析完成，合并后共 {len(df_all)} 条记录")
        return df_all


if __name__ == "__main__":
    sample_signatures = [
        "MNuqWoyfPhZH55bna1KXCygN6WGDXa72bRU9HmRJABd48iEAuLBxgPWkLddJ5krhXsmsejDpXy5oM9c4iyQLj9d",
        "2y9ngxbiFwH3DV398enfTHJSf9vKsrBhoNSYQq86ay8VfjqWqmrxr746R5jFknZQFvjmKG8tHcpyyLoY2w2AVJK5"
    ]
    df_signatures = pd.DataFrame({"signature": sample_signatures})

    decoder = TransactionListDecoder()
    final_result = decoder.decode(df_signatures)

    pd.set_option("display.max_columns", None)
    pd.set_option("display.width", 200)
    pd.set_option("display.float_format", '{:.9f}'.format)
    print(final_result)

    final_result.to_csv("parsed_transactions.csv", index=False)
