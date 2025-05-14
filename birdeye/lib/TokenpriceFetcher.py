from birdeye.lib.common import *

from birdeye.lib.common import *  # 假设已包含 config 和 logger
import pandas as pd
import requests
import time
from datetime import datetime


class TokenpriceFetcher:
    def __init__(self, address_type: str = "token"):
        self.api_key = config.CONFIG["BIRDEYE_APIKEY"]
        self.address_type = address_type
        self.base_url = "https://public-api.birdeye.so/defi/history_price"

    @staticmethod
    def to_timestamp(timestr: str) -> int:
        dt = datetime.strptime(timestr, "%Y-%m-%d %H:%M:%S")
        return int(time.mktime(dt.timetuple()))

    def fetch_price_history(
        self,
        address: str,
        time_from_str: str,
        time_to_str: str,
        time_type: str,
        chain: str,
    ) -> pd.DataFrame | None:
        logger.info(f"query address={address}, chain={chain}, time_type={time_type}, "
                    f"time_from={time_from_str}, time_to={time_to_str}")

        time_from = self.to_timestamp(time_from_str)
        time_to = self.to_timestamp(time_to_str)

        url = (
            f"{self.base_url}"
            f"?address={address}"
            f"&address_type={self.address_type}"
            f"&type={time_type}"
            f"&time_from={time_from}"
            f"&time_to={time_to}"
        )

        headers = {
            "accept": "application/json",
            "x-chain": chain,
            "X-API-KEY": self.api_key
        }

        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            data = response.json()
        except Exception as e:
            logger.error(f"请求失败: {e}")
            return None

        if data.get("success") and "items" in data.get("data", {}):
            df = pd.DataFrame(data["data"]["items"])
            df["datetime"] = df["unixTime"].apply(
                lambda ts: datetime.utcfromtimestamp(ts).isoformat()
            )
            logger.info(f"成功获取 {len(df)} 条价格记录")
            return df
        else:
            logger.warning("接口返回 success=false 或数据为空")
            return None


# 示例调用（可选保留）
if __name__ == "__main__":
    fetcher = TokenpriceFetcher()
    df = fetcher.fetch_price_history(
        address="So11111111111111111111111111111111111111112",
        time_from_str="2024-05-01 00:00:00",
        time_to_str="2024-05-01 01:00:00",
        time_type="1m",
        chain="solana"
    )
    pd.set_option("display.max_columns", None)
    pd.set_option("display.width", 200)
    pd.set_option("display.float_format", '{:.9f}'.format)
    print(df)
