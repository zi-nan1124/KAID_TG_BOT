from typing import List
import asyncio
import httpx
import time

class MySolanaClient:
    def __init__(self, rpc_url: str, max_concurrency: int = 50):
        self.rpc_url = rpc_url
        self.max_concurrency = max_concurrency

    async def _fetch_tx(self, sig: str, client: httpx.AsyncClient, semaphore: asyncio.Semaphore, idx: int):
        payload = {
            "jsonrpc": "2.0",
            "id": idx,
            "method": "getTransaction",
            "params": [sig, {"maxSupportedTransactionVersion": 0}]
        }
        async with semaphore:
            try:
                response = await client.post(self.rpc_url, json=payload)
                return response.json()
            except Exception as e:
                return {"error": str(e), "signature": sig}

    async def get_transaction_by_signature(self, signatures: List[str]):
        semaphore = asyncio.Semaphore(self.max_concurrency)
        async with httpx.AsyncClient(http2=True, timeout=15.0) as client:
            tasks = [
                self._fetch_tx(sig, client, semaphore, idx)
                for idx, sig in enumerate(signatures)
            ]
            results = await asyncio.gather(*tasks)
        return results


# ✅ 测试函数：异步方式调用 get_transaction_by_signature
if __name__ == "__main__":
    async def main():
        rpc_url = "https://lingering-wispy-voice.solana-mainnet.quiknode.pro/6e5fc0da5f61cc165757bcd9c453ab31ba36419a/"
        sample_sig = "3G8tcCeVBDr7M4Bo2ABeLdgPY26x1prbgTAfL171LFGiiaeoiMJ8gwpouFeFM9C8KbFXCvnQto1r7DrUGuT4uff9"
        signatures = [sample_sig for _ in range(100)]

        client = MySolanaClient(rpc_url)
        responses = await client.get_transaction_by_signature(signatures)

        for idx, res in enumerate(responses):
            print(f"--- Response #{idx + 1} ---")
            print(res)

    asyncio.run(main())
