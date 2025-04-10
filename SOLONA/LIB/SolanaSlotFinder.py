from SOLONA.LIB.common import *
import datetime


class SolanaSlotFinder:
    def __init__(self, rpc_url: str, max_error_seconds: int = 500):
        self.client = Client(rpc_url)
        self.max_error_seconds = max_error_seconds
        logger.info(f"✅ SolanaSlotFinder 初始化成功，节点: {rpc_url}")

    def get_block_time(self, slot: int) -> int | None:
        time.sleep(0.02)
        try:
            res = self.client.get_block_time(slot)
            return res.value if hasattr(res, "value") else None
        except RPCException as e:
            logger.warn(f"Slot {slot} 出错: {str(e)}")
            return None

    def get_latest_slot(self) -> int:
        latest = self.client.get_slot()
        return latest.value if hasattr(latest, "value") else 0

    def estimate_slot_by_avg_speed(self, target_timestamp: int, sample_count: int = 100) -> int:
        logger.info(f"📐 基于平均出块速度估算目标 slot: {target_timestamp}")
        current_time = int(time.time())
        current_slot = self.get_latest_slot()
        samples = self.client.get_recent_performance_samples(sample_count).value

        if not samples:
            logger.warn("⚠️ 无 performance samples，使用当前 slot")
            return current_slot

        total_slots = sum(s.num_slots for s in samples)
        total_secs = sum(s.sample_period_secs for s in samples)
        speed = total_slots / total_secs if total_secs else 2.5
        logger.info(f"📊 平均出块速度: {speed:.4f} slots/s")

        delta_secs = target_timestamp - current_time
        estimate_slot = current_slot + int(delta_secs * speed)
        logger.info(f"🧮 估算 slot: {estimate_slot}")
        return estimate_slot

    def find_slot_by_timestamp(self, target_timestamp: int, window: int = 10000) -> tuple[int, int]:
        logger.info(f"🔍 查找目标时间戳对应的 slot: {target_timestamp} ± {window}")
        estimate_slot = self.estimate_slot_by_avg_speed(target_timestamp)

        # 自动偏移起点，避免最左边时间落在目标时间之后
        probe_left = estimate_slot
        while True:
            left_time = self.get_block_time(probe_left)
            if left_time is None or left_time > target_timestamp:
                logger.info(f"↩️ 左移 slot: {probe_left} → {probe_left - window}")
                probe_left -= window
                if probe_left <= 0:
                    probe_left = 1
                    break
            else:
                break

        start = max(1, probe_left)
        end = estimate_slot + window
        closest_slot, closest_err = None, float("inf")

        while start <= end:
            mid = (start + end) // 2
            start_time = self.get_block_time(start)
            mid_time = self.get_block_time(mid)
            end_time = self.get_block_time(end)

            fmt = lambda ts: datetime.datetime.utcfromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S") if ts else "None"
            err = lambda t: abs(t - target_timestamp) if t else None

            logger.info(f"Slot     → [ Left: {start:<10} | Mid: {mid:<10} | Right: {end:<10} ]")
            logger.info(f"Time     → [ Left: {fmt(start_time):<19} | Mid: {fmt(mid_time):<19} | Right: {fmt(end_time):<19} ]")
            logger.info(f"Target   →           {datetime.datetime.utcfromtimestamp(target_timestamp)}")
            logger.info(f"误差(秒) → [ Left: {err(start_time)} | Mid: {err(mid_time)} | Right: {err(end_time)} ]")

            if mid_time is None:
                end = mid - 1
                continue

            mid_err = abs(mid_time - target_timestamp)
            if mid_err < closest_err:
                closest_err = mid_err
                closest_slot = mid
                logger.info(f"✅ 更新最接近 Slot: {closest_slot} (误差 {mid_err} s)")

                # 🎯 满足最大误差限制，提前终止搜索
                if mid_err <= self.max_error_seconds:
                    logger.info(f"🛑 误差已满足条件 ({mid_err} <= {self.max_error_seconds})，提前返回")
                    break

            if mid_time < target_timestamp:
                start = mid + 1
            else:
                end = mid - 1

        if closest_slot:
            match_time = self.get_block_time(closest_slot)
            match_time_str = datetime.datetime.utcfromtimestamp(match_time)
            logger.info(f"🌟 搜索完成！Slot = {closest_slot}, 时间: {match_time_str}, 误差: {closest_err} s")
            return closest_slot, closest_err
        else:
            logger.error("❌ 未找到合适 slot")
            return -1, -1




# 用法示例
if __name__ == "__main__":
    rpc_url = "https://wild-boldest-rain.solana-mainnet.quiknode.pro/b95f33839916945a42159c53ceab4d7468a51a69/"
    finder = SolanaSlotFinder(rpc_url)

    # 指定目标时间
    dt = datetime.datetime(2025, 2, 27, 0, 0)
    ts = int(dt.timestamp())

    slot, err = finder.find_slot_by_timestamp(ts)
    print(f"\n🚀 Slot = {slot}, 时间误差 = {err} s ≈ {err/60:.2f} 分钟")