from SOLONA.LIB.common import *

class PumpFunTradeDecoder:
    TARGET_PROGRAMS = {
        "PUMP_FUN": "pAMMBay6oceH9fJKBRHGP5D4bD4sWpmSwMn52FMfXEA",
        "PUMP_AMM": "6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P"
    }

    def __init__(self):
        pass


    def decode(self, tx_json):
        signature = tx_json["transaction"]["signatures"][0]
        signer = tx_json['transaction']['message']['accountKeys'][0]
        account_keys = tx_json['transaction']['message']['accountKeys']
        logs = tx_json['meta']['logMessages']
        pre_balances = tx_json['meta']['preBalances']
        post_balances = tx_json['meta']['postBalances']
        pre_token_balances = tx_json['meta']['preTokenBalances']
        post_token_balances = tx_json['meta']['postTokenBalances']
        block_time = tx_json.get("blockTime")

        tx_type = self._detect_type(logs)
        tx_protocol = self._detect_protocol(account_keys)

        if not self._is_valid_trade(tx_protocol, tx_type):
            logger.warn(f"交易 {signature} 不满足条件，跳过")
            return None

        token_changes = self._extract_token_change(pre_token_balances, post_token_balances)
        sol_amount = self._extract_sol_change(pre_balances, post_balances)

        if not token_changes:
            logger.error(f"交易:{signature} 没有找到 meme_token 变化")
            return None

        mint, delta = max(token_changes.items(), key=lambda item: abs(item[1]))

        if tx_type == "sell":
            from_token, from_amount = mint, abs(delta)
            to_token, to_amount = "So11111111111111111111111111111111111111112", sol_amount
        else:  # buy
            from_token, from_amount = "So11111111111111111111111111111111111111112", sol_amount
            to_token, to_amount = mint, abs(delta)

        dt = datetime.utcfromtimestamp(block_time).strftime("%Y-%m-%d %H:%M:%S") if block_time else None

        return pd.DataFrame([{
            "user": signer,
            "tx_type": "SWAP",
            "protocol": tx_protocol,
            "signature": signature,
            "timestamp": dt,
            "from_token": from_token,
            "from_amount": from_amount,
            "to_token": to_token,
            "to_amount": to_amount
        }])

    def _detect_protocol(self, account_keys):
        for name, prog in self.TARGET_PROGRAMS.items():
            if prog in account_keys:
                return name
        return "UNKNOWN"

    def _detect_type(self, logs):
        if any("Instruction: Buy" in log for log in logs):
            return "buy"
        elif any("Instruction: Sell" in log for log in logs):
            return "sell"
        return "unknown"

    def _is_valid_trade(self, protocol, tx_type):
        return protocol in {"PUMP_FUN", "PUMP_AMM"} and tx_type in {"buy", "sell"}

    def _extract_token_change(self, pre_token_balances, post_token_balances):
        token_changes = {}
        for pre in pre_token_balances:
            mint = pre['mint']
            owner = pre['owner']
            pre_amt = float(pre['uiTokenAmount']['uiAmount'] or 0.0)
            post = next(
                (p for p in post_token_balances if p['mint'] == mint and p['owner'] == owner),
                None
            )
            post_amt = float(post['uiTokenAmount']['uiAmount']) if post and post['uiTokenAmount']['uiAmount'] else 0.0
            delta = post_amt - pre_amt
            if delta != 0:
                token_changes[mint] = delta
        return token_changes

    def _extract_sol_change(self, pre_balances, post_balances):
        delta = post_balances[0] - pre_balances[0]
        return round(abs(delta) / 1e9, 9)


# 示例主程序
if __name__ == "__main__":
    client = Client("https://api.mainnet-beta.solana.com")
    tx_signature = Signature.from_string("MNuqWoyfPhZH55bna1KXCygN6WGDXa72bRU9HmRJABd48iEAuLBxgPWkLddJ5krhXsmsejDpXy5oM9c4iyQLj9d")
    response = client.get_transaction(tx_signature, max_supported_transaction_version=0)
    if not response.value:
        print("⚠️ 无法获取交易信息")
    else:
        tx_json = json.loads(response.value.to_json())
        decoder = PumpFunTradeDecoder()
        df = decoder.decode(tx_json)
        pd.set_option("display.max_columns", None)
        pd.set_option("display.width", 200)
        pd.set_option("display.float_format", '{:.9f}'.format)
        print(df)
