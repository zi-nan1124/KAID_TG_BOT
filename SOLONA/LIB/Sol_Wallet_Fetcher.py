from SOLONA.LIB.common import *
import datetime
from SOLONA.LIB.SolanaSlotFinder import SolanaSlotFinder
from SOLONA.LIB.TransactionListDecoder import TransactionListDecoder
from SOLONA.LIB.WalletProfitCalculater import WalletProfitCalculater

class SolanaWalletExplorer:
    def __init__(self, rpc_url: str, wallet_address: str):
        self.rpc_url = rpc_url
        self.client = Client(self.rpc_url)
        self.wallet_address = wallet_address
        self.wallet_pubkey = Pubkey.from_string(wallet_address)
        self.wallet_balance = 0
        logger.info(f"初始化 Explorer，地址: {wallet_address}")
        self.standard_7 = 2000

    def get_account_info(self):
        """
        获取账户信息并更新 self.wallet_balance（单位为 SOL）
        """
        account_info = self.client.get_account_info(self.wallet_pubkey)

        if account_info.value:
            logger.info("获取账户信息成功")
            info = account_info.value.to_json()
            info = json.loads(info)

            lamports = info.get("lamports", 0)
            self.wallet_balance = lamports / 1_000_000_000  # 转换为 SOL

            return info
        else:
            logger.warn("未获取到账户信息")
            self.wallet_balance = 0
            return None

    def get_signatures(self):
        all_signatures = []
        before = None

        while True:
            logger.info(f"请求交易签名: limit=1000, before={before}")
            result = self.client.get_signatures_for_address(self.wallet_pubkey, limit=1000, before=before)
            if not result.value:
                logger.info("没有更多交易")
                break

            batch = result.value
            successful = [
                {"signature": str(s.signature)}
                for s in batch if s.err is None
            ]
            logger.info(f"本次获取 {len(batch)} 条，成功 {len(successful)} 条")
            all_signatures.extend(successful)

            if len(successful) == 0:
                logger.info("本次循环无成功交易，终止递归")
                break

            before = batch[-1].signature

        logger.info(f"总共获取成功交易: {len(all_signatures)} 条")
        return pd.DataFrame(all_signatures)


    def get_signatures_by_7days(self):
        all_signatures = []
        before = None
        slot_finder = SolanaSlotFinder(self.rpc_url)
        # 计算七天前的 slot
        now = datetime.datetime.utcnow()
        seven_days_ago = now - datetime.timedelta(days=7)
        target_timestamp = int(seven_days_ago.timestamp())
        #cutoff_slot,err = slot_finder.find_slot_by_timestamp(target_timestamp)
        cutoff_slot = slot_finder.estimate_slot_by_avg_speed(target_timestamp)
        logger.info(f"7天前的时间戳为 {target_timestamp}，对应 Slot 为 {cutoff_slot}")

        while True:
            logger.info(f"请求交易签名: limit=1000, before={before}")
            result = self.client.get_signatures_for_address(self.wallet_pubkey, limit=1000, before=before)
            if not result.value:
                logger.info("没有更多交易")
                break

            batch = result.value
            successful = [
                {"signature": str(s.signature), "slot": s.slot}
                for s in batch if s.err is None
            ]

            logger.info(f"本次获取 {len(batch)} 条，成功 {len(successful)} 条")
            all_signatures.extend(successful)

            if len(successful) == 0:
                logger.info("本次循环无成功交易，终止递归")
                break

            if len(all_signatures) >= self.standard_7:
                logger.warn(f"获取的消息总量超过七日负载最高标准：{self.standard_7} 取消签名获取")
                break

            oldest_slot = min(s["slot"] for s in successful)
            if oldest_slot < cutoff_slot:
                logger.info(f"最旧交易 slot={oldest_slot} < 7天前 slot={cutoff_slot}，终止递归")
                break

            before = batch[-1].signature

        # 保留 slot >= cutoff_slot 的交易
        filtered = [s for s in all_signatures if s["slot"] >= cutoff_slot]
        logger.info(f"最终保留过去7天内的成功交易: {len(filtered)} 条")
        return pd.DataFrame(filtered)[["signature"]]

    async def decode_transaction(self, signature_df: pd.DataFrame) -> pd.DataFrame:
        """
        解析传入的交易签名 DataFrame，返回标准结构 DataFrame。
        参数: signature_df - 包含 "signature" 列的 DataFrame
        """
        logger.info(f"开始解析 {len(signature_df)} 条交易签名")
        if signature_df.empty:
            logger.warn("输入签名为空，跳过解析")
            return pd.DataFrame()

        decoder = TransactionListDecoder()
        decoded_df = await decoder.decode(signature_df)
        return decoded_df


    async def calculate_profit_by_7_day(self):
        logger.info("开始计算过去7天内钱包的盈利情况")
        start_time = time.time()

        try:
            # 第一步：获取7天交易签名
            step1_start = time.time()
            signature_df = self.get_signatures_by_7days()
            step1_end = time.time()

            if len(signature_df) > self.standard_7 :
                return None, None
            if signature_df.empty :
                logger.warn("未获取到近7天的签名，跳过盈利计算")
                return None, None

            # 第二步：解析交易
            step2_start = time.time()
            decoded_df = await self.decode_transaction(signature_df)
            step2_end = time.time()

            if decoded_df.empty:
                logger.warn("没有成功解析的交易，跳过盈利计算")
                return None, None

            # 第三步：调用盈利计算器
            step3_start = time.time()
            calculator = WalletProfitCalculater(self.wallet_address)
            result_df,summary =  calculator.calculate_all_token_profits(decoded_df)

            total_cost = summary.get("total_cost", 0)
            total_profit = summary.get("total_profit", 0)

            if total_profit != 0:
                profit_ratio = total_profit / total_cost
            else:
                profit_ratio = 0
            summary["profit_ratio"] = f"{profit_ratio * 100:.2f}%"
            readable_df = calculator.get_wallet_trade_history(decoded_df)
            print_trade_history_colored(readable_df)
            print(Style.RESET_ALL)
            step3_end = time.time()

            # 打印各步骤耗时信息
            logger.info(f"步骤1 - 获取签名 耗时: {step1_end - step1_start:.2f} 秒")
            logger.info(f"步骤2 - 解码交易 耗时: {step2_end - step2_start:.2f} 秒")
            logger.info(f"步骤3 - 盈利计算 耗时: {step3_end - step3_start:.2f} 秒")
            logger.info(f"总耗时: {time.time() - start_time:.2f} 秒")
            print(result_df)
            print(summary)

            return result_df, summary

        except Exception as e:
            error_detail = traceback.format_exc()
            logger.error(f"计算盈利时出错: {e}\n{error_detail}")
            return None, None


# 示例用法
import asyncio

async def main():
    start_time = time.time()  # 开始计时

    pd.set_option("display.max_columns", None)
    pd.set_option("display.max_rows", None)  # 显示所有行
    pd.set_option("display.width", 200)
    pd.set_option("display.float_format", '{:.9f}'.format)

    rpc_url = config.CONFIG["rpc_url"]
    explorer = SolanaWalletExplorer(
        rpc_url=rpc_url,
        wallet_address="9HCTuTPEiQvkUtLmTZvK6uch4E3pDynwJTbNw6jLhp9z"
    )

    print(f"🔎 查询地址: {explorer.wallet_address}\n")

    account_info = explorer.get_account_info()
    print("\n📋 账户信息对象（原始 JSON）:")
    print(json.dumps(account_info, indent=2) if account_info else "未找到账户信息")

    # 新调用：获取近7天的交易
    #df_recent = explorer.get_signatures_by_7days()
    #print("\n📅 近7天交易签名（DataFrame 表格）:")
    #print(df_recent.head())
    #df_recent.to_csv("wallet_tx_last7days.csv", index=False)

    #print("\n🔍 正在解析近7天的交易详情...")
    #df_tx_details = explorer.decode_transaction(df_recent)
    #print(df_tx_details.head())

    print("\n 正在计算钱包的七日盈利率：")
    result_df, summary = await explorer.calculate_profit_by_7_day()
    #print(result_df)
    #print(summary)

    end_time = time.time()  # 结束计时
    duration = end_time - start_time
    print(f"\n✅ 总共运行时间：{duration:.2f} 秒")

    # 可选保存为 CSV
    #df_tx_details.to_csv("wallet_tx_last7days.csv", index=False)

if __name__ == "__main__":
    asyncio.run(main())
