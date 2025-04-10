import json
from solana.rpc.api import Client
from solders.signature import Signature
from Logger import Logger
from solders.pubkey import Pubkey
import base58

class LogDecoder:
    def __init__(self, rpc_url="https://api.mainnet-beta.solana.com"):
        """
        初始化 LogDecoder 实例，配置 RPC、日志器、常用 mint 映射和 swap 授权地址。
        """
        logger = Logger()
        self.client = Client(rpc_url)
        self.mint_symbol_map = {
            "So11111111111111111111111111111111111111112": "SOL",
            "Es9vMFrzaCERrHL8B9LZpQoeMvsGLPfJxGnaw6Fe3rGU": "USDT",
            "7vfCXT3YPW5p8C3Ur5WFzR9YyNToZoqGcS43GzdmwQpE": "WETH",
        }
        self.swap_authorities = {
            "6uVXuRXk1zprbtNMZxKWT1Y4n1oPA1kYLoz3YMtfYpzz",
            "5quBsrYYXK4y6AeobFsCUgfKP5e3isBkaZrGzjixMEcN",
        }

        # 全局上下文变量
        self.account_map = {}  # index -> address
        self.signer = None
        self.balances = {}

    def fetch_transaction(self, signature: str):
        sig = Signature.from_string(signature)
        resp = self.client.get_transaction(sig, max_supported_transaction_version=0)
        if not resp.value:
            raise ValueError("交易不存在或无法访问")
        return json.loads(resp.value.to_json())

    def parse(self, tx_json):
        self.account_map = self._build_account_index_map(tx_json)
        self.signer = 0
        self.balances = self._extract_balances(tx_json)

        transfers = self._extract_token_transfers(tx_json)
        logger.info(transfers)
        events = self._match_transfers(transfers)
        logger.info(events)
        enriched = [self._enrich_event(e) for e in events]
        logger.info(enriched)
        return enriched

    def _build_account_index_map(self, tx_json):
        msg = tx_json["transaction"]["message"]
        account_keys = msg.get("accountKeys", [])
        loaded = tx_json.get("meta", {}).get("loadedAddresses", {})
        loaded_writable = loaded.get("writable", [])
        loaded_readonly = loaded.get("readonly", [])
        full_keys = account_keys + loaded_writable + loaded_readonly
        return {i: key for i, key in enumerate(full_keys)}

    def _extract_balances(self, tx_json):
        return {
            "pre": tx_json["meta"].get("preTokenBalances", []),
            "post": tx_json["meta"].get("postTokenBalances", [])
        }

    def _is_token_transfer(self, ix):
        logger.info(f"ix:{ix}")

        program_id_index = ix.get("programIdIndex")
        program_id = self.account_map.get(program_id_index)

        logger.info(f"对比指令 : {program_id} 与 TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA")

        if program_id != "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA":
            logger.info("非 SPL Token 程序，跳过该指令")
            return False

        try:
            data_base58 = ix.get("data", "")
            decoded = base58.b58decode(data_base58)
            first_byte = decoded[0]
            logger.info(f"指令 data 解码成功，首字节 = {first_byte}（期望: 3）")
            return first_byte == 3
        except Exception as e:
            logger.warn(f"解码指令数据失败，base64 = {ix.get('data', '')}，错误信息: {e}")
            return False

    def _decode_transfer(self, ix):
        data = base58.b58decode(ix["data"])
        amount = int.from_bytes(data[1:9], "little")
        return {
            "from": ix["accounts"][0],
            "to": ix["accounts"][1],
            "authority": ix["accounts"][2],
            "amount": amount
        }

    def _extract_token_transfers(self, tx_json):
        transfers = []
        for inner in tx_json["meta"].get("innerInstructions", []):
            for ix in inner.get("instructions", []):
                if self._is_token_transfer(ix):
                    transfers.append(self._decode_transfer(ix))
        return transfers

    def _match_transfers(self, transfers):
        events = []
        pending = None
        for t in transfers:
            if pending:
                if (pending["authority"] != t["authority"] and
                    pending["from"] != t["from"] and pending["to"] != t["to"]):
                    events.append({
                        "type": "swap",
                        "from_transfer": pending,
                        "to_transfer": t
                    })
                    pending = None
                    continue
                else:
                    events.append({
                        "type": "transfer",
                        "data": pending,
                        "direction": "out" if pending["from"] == self.signer else "in"
                    })
            pending = t

        if pending:
            events.append({
                "type": "transfer",
                "data": pending,
                "direction": "out" if pending["from"] == self.signer else "in"
            })
        return events

    def _enrich_event(self, event):
        def enrich_token_info(account_index, amount):
            for b in self.balances["pre"] + self.balances["post"]:
                if b["accountIndex"] == account_index:
                    mint = b["mint"]
                    ui_data = b.get("uiTokenAmount")
                    if not ui_data or ui_data.get("decimals") is None:
                        return None
                    decimal = ui_data["decimals"]
                    return {
                        "mint": mint,
                        "symbol": self.mint_symbol_map.get(mint, mint[:4]),
                        "decimal": decimal,
                        "amount": amount,
                        "token_amount": amount / (10 ** decimal)
                    }
            return None

        if event["type"] == "swap":
            from_idx = event["from_transfer"]["from"]
            to_idx = event["to_transfer"]["from"]
            from_amt = event["from_transfer"]["amount"]
            to_amt = event["to_transfer"]["amount"]
            event["from_token"] = enrich_token_info(from_idx, from_amt)
            event["to_token"] = enrich_token_info(to_idx, to_amt)
            del event["from_transfer"]
            del event["to_transfer"]
        else:
            from_idx = event["data"]["from"]
            amt = event["data"]["amount"]
            event["token_info"] = enrich_token_info(from_idx, amt)
            del event["data"]
        return event

if __name__ == "__main__":
    decoder = LogDecoder()
    tx_signature = "GeuLLrzN1bZm9LwxFgmWZ5SBkv13eVk15LHBkLSq4AGuHcW5QRTSgtQueMXHu2YQ8BPfws7srQKZtsvEWZEU9KA"
    tx_json = decoder.fetch_transaction(tx_signature)

    for line in decoder.parse(tx_json):
        print(line)
