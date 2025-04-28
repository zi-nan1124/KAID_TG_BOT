from SOLONA.LIB.common import *
from SOLONA.LIB.HeliusLogDecoder import HeliusLogDecoder
from SOLONA.LIB.PumpFunTradeDecoder import PumpFunTradeDecoder
from SOLONA.LIB.MySolanaClient import MySolanaClient
from multiprocessing import Pool, cpu_count
import asyncio


def decode_single(tx_json):

    decoder = PumpFunTradeDecoder()
    try:
        tx_data = tx_json.get("result")
        if not tx_data:
            Logger().error("tx_json 中缺少 'result' 字段")
            return None

        df = decoder.decode(tx_data)
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
        self.rpc_pool = [config.CONFIG["rpc_url"]] * 4 + [
            config.CONFIG["rpc_url1"],
            config.CONFIG["rpc_url2"],
            config.CONFIG["rpc_url3"]
        ]
        self.client = Client(config.CONFIG["rpc_url"])

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

    async def fetch_pump_tx_json(self, pump_df: pd.DataFrame) -> list:
        logger.info("开始异步获取 PUMP 交易 JSON 数据（按权重分配 RPC）...")

        signatures = pump_df["signature"].tolist()
        if not signatures:
            return []

        weighted_rpc_urls = {
            config.CONFIG["rpc_url"]: 4,
            config.CONFIG["rpc_url1"]: 1,
            config.CONFIG["rpc_url2"]: 1,
            config.CONFIG["rpc_url3"]: 1
        }

        total_weight = sum(weighted_rpc_urls.values())
        rpc_sig_map = {}
        remaining = signatures.copy()

        for url, weight in weighted_rpc_urls.items():
            count = int(len(signatures) * weight / total_weight)
            rpc_sig_map[url] = remaining[:count]
            remaining = remaining[count:]

        first_url = next(iter(weighted_rpc_urls))
        rpc_sig_map[first_url].extend(remaining)

        # 异步调度
        tasks = []
        for url, sigs in rpc_sig_map.items():
            client = MySolanaClient(url)
            tasks.append(client.get_transaction_by_signature(sigs))

        all_results = await asyncio.gather(*tasks, return_exceptions=True)

        results = []
        for i, result in enumerate(all_results):
            if isinstance(result, Exception):
                logger.error(f"第 {i} 个 RPC 获取失败: {result}")
                continue
            valid = [tx for tx in result if "result" in tx]
            logger.info(f"第 {i} 个 RPC 成功获取 {len(valid)} 条交易")
            results.extend(valid)

        return results

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

    async def decode(self, sig_df: pd.DataFrame) -> pd.DataFrame:
        logger.info("开始全流程解析（异步）...")
        df_others, df_pump_init = self.parse_signatures(sig_df)
        tx_jsons = await self.fetch_pump_tx_json(df_pump_init)
        df_pump_decoded = self.decode_pump_multithreaded(tx_jsons)  # 保留 CPU 多进程解析
        df_all = self.merge_results(df_others, df_pump_decoded)
        return df_all



async def run_test_from_csv(csv_path="test.csv", output_path="parsed_transactions.csv"):
    # 读取签名 CSV 文件
    df_signatures = pd.read_csv(csv_path)
    if "signature" not in df_signatures.columns:
        print("[❌] CSV 文件缺少 signature 列")
        return

    pd.set_option("display.max_columns", None)
    pd.set_option("display.width", 200)
    pd.set_option("display.float_format", '{:.9f}'.format)

    num_sigs = len(df_signatures)
    print(f"[⏱️] 开始解析 {num_sigs} 条签名交易...")
    start_time = time.time()

    decoder = TransactionListDecoder()
    final_result = await decoder.decode(df_signatures)

    elapsed = time.time() - start_time
    print(f"[✅] 解析完成，用时 {elapsed:.2f} 秒")

    # 输出简要信息
    print(f"[📊] 总记录数: {len(final_result)}")
    if not final_result.empty and "protocol" in final_result.columns:
        print(f"[📦] 涉及协议: {final_result['protocol'].unique().tolist()}")

    final_result.to_csv(output_path, index=False)
    print(f"[💾] 已保存至: {output_path}")

    print("\n--- 部分记录预览 ---")
    print(final_result.head(5))
    return final_result


if __name__ == "__main__":
    asyncio.run(run_test_from_csv())



