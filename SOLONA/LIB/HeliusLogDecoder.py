from SOLONA.LIB.common import *



class HeliusLogDecoder:
    def __init__(self):
        self.api_key = config.CONFIG["HELIU_APIKEY"]
        self.base_url = f"https://api.helius.xyz/v0/transactions/?api-key={self.api_key}"

    def batch_parse_transactions(self, signatures: list) -> list:
        """对大于100的列表分批，每批最多100个请求"""
        all_results = []
        chunk_size = 100
        num_batches = ceil(len(signatures) / chunk_size)

        for i in range(num_batches):
            batch = signatures[i * chunk_size:(i + 1) * chunk_size]
            headers = {"Content-Type": "application/json"}
            payload = {"transactions": batch}

            response = requests.post(self.base_url, headers=headers, json=payload)
            if response.status_code != 200:
                logger.error(f"第{i+1}/{num_batches}批请求失败: {response.status_code} {response.text}")
                continue

            batch_data = response.json()
            all_results.extend(batch_data)

        return all_results

    def summarize(self, tx: dict) -> dict:
        tx_type = tx.get("type", "UNKNOWN")
        user = tx.get("feePayer")
        signature = tx.get("signature")
        protocol = tx.get("source", "HELIUS")
        fee = tx.get("fee", 0) / 1e9

        block_time = tx.get("timestamp")  # Helius 返回的是 timestamp (秒)
        dt = datetime.utcfromtimestamp(block_time).strftime("%Y-%m-%d %H:%M:%S") if block_time else None

        from_token = "UNKNOWN"
        from_amount = 0.0
        to_token = "UNKNOWN"
        to_amount = 0.0

        if tx_type == "SWAP":
            swap = tx.get("events", {}).get("swap", {})
            if swap.get("nativeInput"):
                from_token = "So11111111111111111111111111111111111111112"
                from_amount = int(swap["nativeInput"]["amount"]) / 1e9
            elif swap.get("tokenInputs"):
                t = swap["tokenInputs"][0]
                from_token = t["mint"]
                from_amount = int(t["rawTokenAmount"]["tokenAmount"]) / (10 ** t["rawTokenAmount"]["decimals"])

            if swap.get("nativeOutput"):
                to_token = "So11111111111111111111111111111111111111112"
                to_amount = int(swap["nativeOutput"]["amount"]) / 1e9
            elif swap.get("tokenOutputs"):
                t = swap["tokenOutputs"][0]
                to_token = t["mint"]
                to_amount = int(t["rawTokenAmount"]["tokenAmount"]) / (10 ** t["rawTokenAmount"]["decimals"])

        elif tx_type == "TRANSFER":
            transfers = tx.get("nativeTransfers", [])
            if transfers:
                t = transfers[0]
                from_token = to_token = "So11111111111111111111111111111111111111112"
                from_amount = to_amount = int(t["amount"]) / 1e9

        return {
            "user": user,
            "tx_type": "SWAP" if tx_type == "SWAP" else tx_type,
            "protocol": protocol,
            "signature": signature,
            "timestamp": dt,
            "from_token": from_token,
            "from_amount": from_amount,
            "to_token": to_token,
            "to_amount": to_amount
        }


if __name__ == "__main__":
    decoder = HeliusLogDecoder()

    # 模拟一堆签名，超过 100 会自动分批
    signature_df = pd.DataFrame({
        "signature": [
            "2y9ngxbiFwH3DV398enfTHJSf9vKsrBhoNSYQq86ay8VfjqWqmrxr746R5jFknZQFvjmKG8tHcpyyLoY2w2AVJK5",
            "MNuqWoyfPhZH55bna1KXCygN6WGDXa72bRU9HmRJABd48iEAuLBxgPWkLddJ5krhXsmsejDpXy5oM9c4iyQLj9d",
            "51bEpipqa9Hi4yjCHzjebivNKvijkM6nWoePVRzyPSzz7HSoAkwqvi6qHQ55SrZgMn7HNkK6FzV6DSFR9K1sGpBr"
        ] * 60  # 模拟重复 120 条
    })

    signatures = signature_df["signature"].tolist()

    transactions = decoder.batch_parse_transactions(signatures)
    df = pd.DataFrame([decoder.summarize(tx) for tx in transactions if tx])

    pd.set_option("display.max_columns", None)
    pd.set_option("display.width", 200)
    pd.set_option("display.float_format", '{:.9f}'.format)
    print(df)
    df.to_csv("test.csv", index=False)
