from SOLONA.LIB.common import *
from SOLONA.LIB.TokenPriceFetcher import TokenPriceFetcher

class WalletProfitCalculater:
    def __init__(self, wallet_address: str):
        """
        初始化计算器，包含成本币种、默认价格、SOL 当前价格抓取。
        """
        self.wallet_address = wallet_address
        self.price_fetcher = TokenPriceFetcher()
        self._init_cost_tokens()
        self._init_price_map()
        self._update_sol_price()
        self._update_wallet_balance()



    def _init_cost_tokens(self):
        """
        初始化默认成本币种地址集合。
        """
        self.cost_token_addresses = {
            "So11111111111111111111111111111111111111112",  # SOL
            "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v", # USDC
            "Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB"  # USDT
        }

    def _init_price_map(self):
        """
        初始化价格映射表，稳定币为 1，SOL 初始为 0。
        """
        self.price_map = {
            "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v": 1.0,
            "Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB": 1.0,
            "So11111111111111111111111111111111111111112": 0.0,
            "UNKNOWN": 0.0,
        }

    def _update_sol_price(self):
        """
        通过 BirdEye 接口获取当前 SOL 价格，更新 price_map。
        """
        sol_price = self.price_fetcher.fetch_SOL_price()
        if sol_price:
            self.price_map["So11111111111111111111111111111111111111112"] = sol_price
            logger.info(f"SOL 当前价格设置为 {sol_price:.4f} USD")
        else:
            logger.warn("SOL 价格获取失败，使用默认值 0")

    def _update_wallet_balance(self):
        token_list = self.price_fetcher.fetch_wallet_token_list(self.wallet_address)
        self.wallet_token_balance = dict(zip(token_list["token_address"], token_list["token_balance"]))


    def update_price(self, token_address: str, price: float):
        """
        手动设置指定 token 的价格。

        参数：
        - token_address: str，Token mint 地址或符号
        - price: float，USD 计价的价格
        """
        self.price_map[token_address] = price

    def _get_swap_df(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        从原始 DataFrame 中提取所有类型为 SWAP 的交易。

        输入：
        - df: 原始交易记录 DataFrame

        输出：
        - DataFrame，仅包含 SWAP 类型的交易记录
        """
        return df[df['tx_type'].str.upper() == 'SWAP'].copy()

    def _get_all_token_addresses(self, swap_df: pd.DataFrame) -> List[str]:
        """
        提取 SWAP 中所有出现过的 token 地址。

        输入：
        - swap_df: 仅包含 SWAP 的 DataFrame

        输出：
        - List[str]，所有 token 地址（去重）
        """
        return pd.concat([swap_df['from_token'], swap_df['to_token']]).dropna().unique().tolist()

    def _get_non_cost_tokens(self, tokens: List[str]) -> List[str]:
        """
        过滤掉成本币，获取非成本币 token 列表。

        输入：
        - tokens: 所有 token 地址

        输出：
        - List[str]，非成本币 token 地址
        """
        return [t for t in tokens if t not in self.cost_token_addresses]

    def _get_token_price(self, token: str) -> float:
        """
        获取指定 token 的价格，若不存在则返回 0。

        输入：
        - token: token 地址

        输出：
        - float，该 token 的价格
        """
        return self.price_map.get(token, 0.0)

    def _get_token_related_swaps(self, token: str, swap_df: pd.DataFrame) -> pd.DataFrame:
        """
        获取与指定 token 地址有关的所有 SWAP 交易。

        输入：
        - token: token 地址
        - swap_df: 所有 swap 的交易记录

        输出：
        - DataFrame，包含该 token 的所有相关交易
        """
        return swap_df[(swap_df['from_token'] == token) | (swap_df['to_token'] == token)].copy()

    def _update_price_map_from_tokens(self, token_list: List[str]):
        """
        从 BirdEye 批量获取 token 最新价格，更新 price_map。
        """
        df = pd.DataFrame({'address': token_list})
        prices = self.price_fetcher.fetch_prices(df)
        for _, row in prices.iterrows():
            self.price_map[row['address']] = row['price']


    def _get_unrealized_income(self, token: str) -> float:
        """
        计算某个 token 的未实现收入（当前余额 * 当前价格）。
        """
        balance = self.wallet_token_balance.get(token, 0.0)
        price = self._get_token_price(token)
        return balance * price

    def _calculate_token_profit(self, token: str, swap_df: pd.DataFrame) -> Dict:
        """
        计算指定 token 的成本、已实现收入、未实现收入、交易数和盈利。

        输入：
        - token: token 地址
        - swap_df: 所有 SWAP 的 DataFrame

        输出：
        - Dict，包含该 token 的统计信息
        """
        related = self._get_token_related_swaps(token, swap_df)
        tx_count = len(related)
        cost = 0.0
        income = 0.0

        for _, row in related.iterrows():
            from_token = row['from_token']
            to_token = row['to_token']
            from_amount = float(row['from_amount'])
            to_amount = float(row['to_amount'])

            # 买入 token（from 是成本币，to 是目标 token）
            if to_token == token and from_token in self.cost_token_addresses:
                cost += from_amount * self._get_token_price(from_token)

            # 卖出 token（from 是目标 token，to 是成本币）
            if from_token == token and to_token in self.cost_token_addresses:
                income += to_amount * self._get_token_price(to_token)

        unrealized = self._get_unrealized_income(token)

        return {
            "token": token,
            "tx_count": tx_count,
            "cost": cost,
            "realized_income": income,
            "unrealized_income": unrealized,
            "profit": income + unrealized - cost
        }

    def calculate_all_token_profits(self, df: pd.DataFrame) -> (pd.DataFrame, Dict):
        """
        主函数：从原始数据中提取所有非成本币，更新价格、余额，并计算每个币种的盈利汇总。

        输入：
        - df: 原始 DataFrame（需包含 tx_type, from_token, to_token, from_amount, to_amount）

        输出：
        - Tuple:
            - pd.DataFrame：每个非成本币种的盈利明细
            - dict：总交易数、总成本、总收入、总盈利
        """
        swap_df = self._get_swap_df(df)
        all_tokens = self._get_all_token_addresses(swap_df)
        non_cost_tokens = self._get_non_cost_tokens(all_tokens)

        self._update_price_map_from_tokens(non_cost_tokens)

        results = []
        total_tx = total_cost = total_realized = total_unrealized = total_profit = 0.0

        for token in non_cost_tokens:
            result = self._calculate_token_profit(token, swap_df)
            results.append(result)

            total_tx += result["tx_count"]
            total_cost += result["cost"]
            total_realized += result["realized_income"]
            total_unrealized += result["unrealized_income"]
            total_profit += result["profit"]

        summary = {
            "total_tx_count": total_tx,
            "total_cost": total_cost,
            "total_realized": total_realized,
            "total_unrealized": total_unrealized,
            "total_profit": total_profit
        }

        return pd.DataFrame(results), summary


    def get_wallet_trade_history(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        获取该钱包的 SWAP 交易历史，按时间倒序排序，并解析为可读数据。

        输出字段包括：时间、方向（买入/卖出）、token、数量、价值
        """
        swap_df = self._get_swap_df(df)
        swap_df = swap_df.sort_values(by='timestamp', ascending=False).copy()

        readable = []
        for _, row in swap_df.iterrows():
            from_token = row['from_token']
            to_token = row['to_token']
            from_amount = float(row['from_amount'])
            to_amount = float(row['to_amount'])
            timestamp = row['timestamp']

            # 判断方向
            if from_token in self.cost_token_addresses:
                direction = "买入"
                token = to_token
                amount = to_amount
                value = from_amount * self._get_token_price(from_token)
            elif to_token in self.cost_token_addresses:
                direction = "卖出"
                token = from_token
                amount = from_amount
                value = to_amount * self._get_token_price(to_token)
            else:
                direction = "未知"
                token = from_token
                amount = from_amount
                value = 0.0

            readable.append({
                "时间": timestamp,
                "方向": direction,
                "Token": token,
                "数量": amount,
                "价值(USD)": value
            })

        return pd.DataFrame(readable)

if __name__ == "__main__":
    start_time = time.time()

    df = pd.read_csv("profit.csv")
    wallet_address = "DW1DdpQ9JGY4up2yRSg8gKeH9ZwG9xXvywgA6GfWo99a"
    calc = WalletProfitCalculater(wallet_address)

    result_df, summary = calc.calculate_all_token_profits(df)
    readable_df = calc.get_wallet_trade_history(df)
    readable_df.to_csv("wallet_trades.csv", index=False, encoding="utf-8-sig")

    pd.set_option("display.max_columns", None)
    pd.set_option("display.max_rows", None)  # 显示所有行
    pd.set_option("display.width", 200)
    pd.set_option("display.float_format", '{:.9f}'.format)


    print(result_df)
    print("\n===== 总盈利汇总 =====")
    print(summary)

    print("\n===== 交易记录  =====")
    print_trade_history_colored(readable_df)

    end_time = time.time()
    print(f"\n✅ 总共运行时间：{end_time - start_time:.2f} 秒")
