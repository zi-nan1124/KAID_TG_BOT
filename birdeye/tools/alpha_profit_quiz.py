import pandas as pd
from datetime import datetime, timedelta
from birdeye.lib.TokenpriceFetcher import TokenpriceFetcher

# 链映射
CHAIN_MAPPING = {
    "BSC": "bsc",
    "BASE": "base",
    "SOL": "solana"
}

# 初始化 fetcher
fetcher = TokenpriceFetcher()

# 读取原始 Excel 文件
CSV_PATH = "old.xlsx"
df = pd.read_excel(CSV_PATH)

# 修复“登记时间”字段格式
if pd.api.types.is_numeric_dtype(df["登记时间"]):
    df["登记时间"] = pd.to_datetime(df["登记时间"], unit='D', origin='1899-12-30')
else:
    df["登记时间"] = pd.to_datetime(df["登记时间"], errors='coerce')

# 初始化新列
for day in [0, 1, 2, 7]:
    df[f"登记后{day}天价格"] = None

# 遍历每行数据
for idx, row in df.iterrows():
    address = str(row["合约地址"]).strip()
    chain_raw = str(row["链"]).strip().upper()
    chain = CHAIN_MAPPING.get(chain_raw)
    base_time = row["登记时间"]

    # 跳过无效链或时间
    if chain is None or pd.isna(base_time):
        continue

    for delta in [0, 1, 2, 7]:
        dt = (base_time + timedelta(days=delta)).replace(hour=23, minute=59, second=0)
        dt_str = dt.strftime("%Y-%m-%d %H:%M:%S")

        try:
            price_df = fetcher.fetch_price_history(
                address=address,
                time_from_str=dt_str,
                time_to_str=dt_str,
                time_type="1m",
                chain=chain
            )

            if not price_df.empty:
                price_value = price_df.iloc[0]["value"]
                df.loc[idx, f"登记后{delta}天价格"] = price_value

        except Exception as e:
            print(f"❌ 错误：地址 {address} 时间 {dt_str} 获取失败：{e}")
            continue

# 保存结果
output_path = "processed_price_data.xlsx"
df.to_excel(output_path, index=False)
print(f"✅ 数据处理完成，已保存到 {output_path}")
