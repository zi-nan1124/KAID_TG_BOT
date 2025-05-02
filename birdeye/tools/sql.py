import pandas as pd

# === 参数配置 ===
CSV_PATH = "filtered_tokens.csv"  # 刚才保存的文件
OUTPUT_PATH = "alpha_delete_sqls.txt"    # 生成的SQL文件

CLUSTER = "biz-dex-evm"
DATABASE = "dexx_data_flow_v4"

CHAIN_ID_MAPPING = {
    "BSC": 56,
    "SOL": 100000,
    "BASE": 8453
}

# === 读取数据 ===
df = pd.read_csv(CSV_PATH)

# === 生成 SQL ===
delete_sqls = []
insert_sqls = []

# 遍历每行生成 DELETE 和 INSERT
for idx, row in df.iterrows():
    token_address = str(row["合约地址"]).replace("'", "''")  # 转义单引号
    token_name = str(row["币种"]).replace("'", "''")        # 转义单引号
    chain = row["链"]

    # 获取对应的 chain_id
    chain_id = CHAIN_ID_MAPPING.get(chain)
    if chain_id is None:
        print(f"⚠️ 未知链：{chain}，跳过 {token_address}")
        continue

    delete_sql = f"DELETE FROM trending_alpha_config WHERE chain_id = {chain_id} AND token_address = '{token_address}';"
    insert_sql = f"INSERT INTO trending_alpha_config(chain_id, token_address, token_name) VALUES ({chain_id}, '{token_address}', '{token_name}');"

    delete_sqls.append(delete_sql)
    insert_sqls.append(insert_sql)

# === 保存到文件 ===
with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
    f.write(f"集群：{CLUSTER}\n")
    f.write(f"数据库：{DATABASE}\n")
    f.write("SQL：\n")
    for sql in delete_sqls:
        f.write(sql + "\n")
    f.write("\n回滚：\n")
    for sql in insert_sqls:
        f.write(sql + "\n")

print(f"✅ SQL 文件已生成：{OUTPUT_PATH}（已处理单引号转义）")
