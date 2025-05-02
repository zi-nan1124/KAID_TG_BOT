import pandas as pd

# === 参数配置 ===
ORIGINAL_XLS_PATH = "test.xlsx"          # 原始输入文件
FILTERED_CSV_PATH = "filtered_tokens.csv"  # 刚才市值筛完的小币种列表
OUTPUT_XLS_PATH = "update_state.xlsx"    # 输出的新文件

# === 第一步：读取原始xls数据 ===
original_df = pd.read_excel(ORIGINAL_XLS_PATH)

# === 第二步：读取filtered csv的数据 ===
filtered_df = pd.read_csv(FILTERED_CSV_PATH)

# 提取需要下架的币种（按合约地址来匹配）
tokens_to_delist = filtered_df["合约地址"].tolist()

# === 第三步：修改状态 ===
# 对原数据中合约地址在 tokens_to_delist 列表里的行，把状态改为"已下架"
original_df.loc[original_df["合约地址"].isin(tokens_to_delist), "状态"] = "已下架"

# === 第四步：保存为新的xls文件 ===
# 保存前，强制把登记时间格式化为 yyyy-mm-dd
original_df["登记时间"] = pd.to_datetime(original_df["登记时间"]).dt.strftime("%Y-%m-%d")
original_df.to_excel(OUTPUT_XLS_PATH, index=False)

print(f"✅ 已成功生成更新状态后的文件：{OUTPUT_XLS_PATH}")
