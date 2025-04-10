from solana.rpc.api import Client
from solders.signature import Signature
import json
from datetime import datetime
import base58
import struct


# ========== 解码 SPL Token 指令 ========== #
def decode_spl_token_instruction(data_base58):
    try:
        raw = base58.b58decode(data_base58)
        if len(raw) == 0:
            return "（空指令）"

        opcode = raw[0]
        if opcode == 3:
            amount = struct.unpack("<Q", raw[1:9])[0]
            return f"Instruction: Transfer\n    Amount: {amount} (in base unit)"
        elif opcode == 1:
            return "Instruction: InitializeAccount"
        elif opcode == 9:
            return "Instruction: CloseAccount"
        elif opcode == 7:
            return "Instruction: MintTo"
        elif opcode == 12:
            return "Instruction: SyncNative"
        else:
            return f"Unknown opcode: {opcode} ({raw.hex()})"
    except Exception as e:
        return f"（解码失败：{e}）"

# ========== 初始化 Solana 客户端 ========== #
client = Client("https://api.mainnet-beta.solana.com")
tx_signature = Signature.from_string("21YuCoLJhKM3N6MFzXnaSnmsMUZFa9by7CUVXutbNtFHr9U8nxpsYpxLTDCP3K5N48p49Y3UaFxzxxM2KEv2bZMy")
response = client.get_transaction(tx_signature, max_supported_transaction_version=0)
tx_json = json.loads(response.value.to_json())
if not response.value:
    print("⚠️ 无法获取交易信息（可能已过期或签名错误）")
    exit()

# ========== 解析 JSON 数据结构 ========== #

meta = tx_json["meta"]
msg = tx_json["transaction"]["message"]
account_keys = msg["accountKeys"]
instructions = msg["instructions"]

# address table 扩展
loaded = meta.get("loadedAddresses", {})
loaded_writable = loaded.get("writable", [])
loaded_readonly = loaded.get("readonly", [])
full_account_keys = account_keys + loaded_writable + loaded_readonly

# ========== 基础信息 ========== #
print("\n===== 🧠 基础信息 =====")
print(f"签名: {tx_signature}")
print(f"Slot: {tx_json['slot']}")
print(f"区块时间: {datetime.fromtimestamp(tx_json['blockTime'])}")
print(f"版本: {tx_json['version']}")
status = "✅ 成功" if meta["err"] is None else f"❌ 失败: {meta['err']}"
print(f"状态: {status}")
print(f"交易费用: {meta['fee']} lamports")
print(f"计算资源消耗: {meta.get('computeUnitsConsumed', 'N/A')}")

# ========== 账户列表 ========== #
print("\n===== 🧾 账户信息 =====")
for i, acc in enumerate(full_account_keys):
    print(f"[{i}] {acc}")

# ========== lamport 余额变化 ========== #
print("\n===== 💰 lamport 余额变化 =====")
for i in range(len(meta["preBalances"])):
    if i < len(full_account_keys):
        pre = meta["preBalances"][i]
        post = meta["postBalances"][i]
        delta = post - pre
        if delta != 0:
            print(f"{full_account_keys[i]}: {pre} → {post} ({'+' if delta > 0 else ''}{delta})")

# ========== Token 余额变化 ========== #
print("\n===== 🪙 Token 账户变化 =====")
for tb in meta.get("preTokenBalances", []):
    idx = tb["accountIndex"]
    if idx < len(full_account_keys):
        print(f"PRE [{full_account_keys[idx]}] mint={tb['mint']}, owner={tb['owner']}, balance={tb['uiTokenAmount']['uiAmountString']}")
for tb in meta.get("postTokenBalances", []):
    idx = tb["accountIndex"]
    if idx < len(full_account_keys):
        print(f"POST [{full_account_keys[idx]}] mint={tb['mint']}, owner={tb['owner']}, balance={tb['uiTokenAmount']['uiAmountString']}")

# ========== 外部指令 ========== #
print("\n===== 📜 指令（外部） =====")
for i, instr in enumerate(instructions):
    pid_idx = instr["programIdIndex"]
    pid = full_account_keys[pid_idx] if pid_idx < len(full_account_keys) else f"(越界:{pid_idx})"
    accounts = [full_account_keys[a] if a < len(full_account_keys) else f"(越界:{a})" for a in instr["accounts"]]
    print(f"Instruction {i+1}:")
    print(f"  - Program: {pid}")
    print(f"  - Accounts: {accounts}")
    print(f"  - Data (base58): {instr['data']}")
    if pid == "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA":
        decoded = decode_spl_token_instruction(instr["data"])
        print(f"  - Decoded: {decoded}")

# ========== 内部指令（innerInstructions） ========== #
if "innerInstructions" in meta and meta["innerInstructions"]:
    print("\n===== 🧬 内部指令（innerInstructions） =====")
    for inner in meta["innerInstructions"]:
        print(f"\nInner Instruction at index {inner['index']}:")
        for instr in inner["instructions"]:
            pid_idx = instr["programIdIndex"]
            pid = full_account_keys[pid_idx] if pid_idx < len(full_account_keys) else f"(越界:{pid_idx})"
            accounts = [full_account_keys[a] if a < len(full_account_keys) else f"(越界:{a})" for a in instr["accounts"]]
            print(f"  - Program: {pid}")
            print(f"  - Accounts: {accounts}")
            print(f"  - Data: {instr['data']}")
            if pid == "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA":
                decoded = decode_spl_token_instruction(instr["data"])
                print(f"    - Decoded: {decoded}")

# ========== 日志输出 ========== #
print("\n===== 🧾 执行日志 =====")
for log in meta.get("logMessages", []):
    print(f"  {log}")

# ========== 动态加载地址表 ========== #
if loaded_writable or loaded_readonly:
    print("\n===== 🧭 动态加载地址（loadedAddresses） =====")
    if loaded_writable:
        print("Writable:")
        for addr in loaded_writable:
            print(f"  - {addr}")
    if loaded_readonly:
        print("Readonly:")
        for addr in loaded_readonly:
            print(f"  - {addr}")

# ========== addressTableLookups ========== #
if "addressTableLookups" in msg and msg["addressTableLookups"]:
    print("\n===== 📖 地址表查找（addressTableLookups） =====")
    for atl in msg["addressTableLookups"]:
        print(f"Address Table Account: {atl['accountKey']}")
        print(f"  Writable Indexes: {atl['writableIndexes']}")
        print(f"  Readonly Indexes: {atl['readonlyIndexes']}")

# ========== 奖励信息 ========== #
if "rewards" in meta and meta["rewards"]:
    print("\n===== 🎁 奖励信息 =====")
    for r in meta["rewards"]:
        print(f"- {r['pubkey']}: {r['lamports']} lamports, type={r['rewardType']}")

print("\n===== ✅ 全部字段解析完毕 =====")
