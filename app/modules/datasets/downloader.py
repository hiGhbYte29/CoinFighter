from collections.abc import Awaitable, Callable

from app.infrastructure.providers.base import MarketDataProvider
from app.modules.market.timeframes import timeframe_milliseconds

ProgressCallback = Callable[[int, str], Awaitable[None]]


async def download_candles(
    provider: MarketDataProvider,
    symbol: str,
    timeframe: str,
    start_ms: int,
    end_ms: int,
    on_progress: ProgressCallback,
) -> list[dict]:
    step = timeframe_milliseconds(timeframe)
    cursor = start_ms
    collected: dict[int, dict] = {}
    while cursor < end_ms:
        batch = await provider.get_candles(symbol, timeframe, since_ms=cursor, limit=1000)
        if not batch:
            break
        for candle in batch:
            timestamp = int(candle["timestamp"])
            if start_ms <= timestamp < end_ms:
                collected[timestamp] = candle
        next_cursor = int(batch[-1]["timestamp"]) + step
        if next_cursor <= cursor:
            break
        cursor = next_cursor
        progress = min(99, int((min(cursor, end_ms) - start_ms) / (end_ms - start_ms) * 100))
        await on_progress(progress, f"已获取 {len(collected):,} 根 K 线")
        if len(batch) < 1000:
            break
    return [collected[key] for key in sorted(collected)]
