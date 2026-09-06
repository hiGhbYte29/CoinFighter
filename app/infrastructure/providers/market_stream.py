import asyncio
import json
import logging
from collections.abc import AsyncIterator
from dataclasses import dataclass
from typing import Literal

from websockets.asyncio.client import connect

from app.core.exceptions import AppError
from app.modules.market.schemas import Candle

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class MarketStreamEvent:
    kind: Literal["candle", "trade"]
    event_time: int
    candle: Candle | None = None
    price: float | None = None
    amount: float | None = None


def _compact_symbol(symbol: str) -> str:
    return symbol.split(":", 1)[0].replace("/", "").replace("-", "").upper()


class MarketStreamService:
    """Native public WebSocket adapters; CCXT remains the REST/history provider."""

    async def stream(
        self, provider: str, market_type: str, symbol: str, timeframe: str
    ) -> AsyncIterator[MarketStreamEvent]:
        provider = provider.lower()
        if market_type != "spot":
            raise AppError(
                "MARKET_STREAM_UNSUPPORTED",
                "实时图表第一版仅支持现货市场",
                status_code=422,
            )
        factories = {
            "binance": self._binance,
            "okx": self._okx,
            "bybit": self._bybit,
        }
        factory = factories.get(provider)
        if factory is None:
            raise AppError(
                "MARKET_STREAM_UNSUPPORTED",
                f"{provider} 暂不支持实时 K 线",
                status_code=422,
            )
        delay = 1.0
        while True:
            try:
                async for event in factory(symbol, timeframe):
                    delay = 1.0
                    yield event
            except asyncio.CancelledError:
                raise
            except AppError:
                raise
            except Exception as error:
                logger.warning("%s 实时行情连接中断，%.1f 秒后重连: %s", provider, delay, error)
                await asyncio.sleep(delay)
                delay = min(delay * 2, 15.0)

    async def _binance(self, symbol: str, timeframe: str) -> AsyncIterator[MarketStreamEvent]:
        compact = _compact_symbol(symbol).lower()
        streams = f"{compact}@kline_{timeframe}/{compact}@trade"
        url = f"wss://stream.binance.com:9443/stream?streams={streams}"
        async with connect(url, ping_interval=20, ping_timeout=20, close_timeout=5) as socket:
            async for raw in socket:
                payload = json.loads(raw)
                data = payload.get("data", payload)
                if data.get("e") == "kline":
                    row = data["k"]
                    candle = Candle(
                        timestamp=int(row["t"]),
                        open=float(row["o"]),
                        high=float(row["h"]),
                        low=float(row["l"]),
                        close=float(row["c"]),
                        volume=float(row["v"]),
                        is_closed=bool(row["x"]),
                    )
                    yield MarketStreamEvent(
                        kind="candle",
                        event_time=int(data.get("E", row["t"])),
                        candle=candle,
                    )
                elif data.get("e") == "trade":
                    yield MarketStreamEvent(
                        kind="trade",
                        event_time=int(data["T"]),
                        price=float(data["p"]),
                        amount=float(data["q"]),
                    )

    async def _okx(self, symbol: str, timeframe: str) -> AsyncIterator[MarketStreamEvent]:
        channel_intervals = {
            "1m": "1m",
            "5m": "5m",
            "15m": "15m",
            "1h": "1H",
            "4h": "4H",
            "1d": "1Dutc",
        }
        interval = channel_intervals.get(timeframe)
        if interval is None:
            raise AppError(
                "TIMEFRAME_UNSUPPORTED",
                f"OKX 实时行情不支持周期 {timeframe}",
                status_code=422,
            )
        instrument = symbol.split(":", 1)[0].replace("/", "-").upper()
        url = "wss://ws.okx.com:8443/ws/v5/business"
        async with connect(url, ping_interval=20, ping_timeout=20, close_timeout=5) as socket:
            await socket.send(
                json.dumps(
                    {
                        "op": "subscribe",
                        "args": [{"channel": f"candle{interval}", "instId": instrument}],
                    }
                )
            )
            async for raw in socket:
                payload = json.loads(raw)
                for row in payload.get("data", []):
                    candle = Candle(
                        timestamp=int(row[0]),
                        open=float(row[1]),
                        high=float(row[2]),
                        low=float(row[3]),
                        close=float(row[4]),
                        volume=float(row[5]),
                        is_closed=str(row[8]) == "1",
                    )
                    yield MarketStreamEvent(kind="candle", event_time=int(row[0]), candle=candle)

    async def _bybit(self, symbol: str, timeframe: str) -> AsyncIterator[MarketStreamEvent]:
        intervals = {
            "1m": "1",
            "5m": "5",
            "15m": "15",
            "1h": "60",
            "4h": "240",
            "1d": "D",
        }
        interval = intervals.get(timeframe)
        if interval is None:
            raise AppError(
                "TIMEFRAME_UNSUPPORTED",
                f"Bybit 实时行情不支持周期 {timeframe}",
                status_code=422,
            )
        compact = _compact_symbol(symbol)
        url = "wss://stream.bybit.com/v5/public/spot"
        topics = [f"kline.{interval}.{compact}", f"publicTrade.{compact}"]
        async with connect(url, ping_interval=20, ping_timeout=20, close_timeout=5) as socket:
            await socket.send(json.dumps({"op": "subscribe", "args": topics}))
            async for raw in socket:
                payload = json.loads(raw)
                topic = str(payload.get("topic", ""))
                if topic.startswith("kline."):
                    for row in payload.get("data", []):
                        candle = Candle(
                            timestamp=int(row["start"]),
                            open=float(row["open"]),
                            high=float(row["high"]),
                            low=float(row["low"]),
                            close=float(row["close"]),
                            volume=float(row["volume"]),
                            is_closed=bool(row["confirm"]),
                        )
                        yield MarketStreamEvent(
                            kind="candle",
                            event_time=int(row.get("timestamp", payload.get("ts", row["start"]))),
                            candle=candle,
                        )
                elif topic.startswith("publicTrade."):
                    for row in payload.get("data", []):
                        yield MarketStreamEvent(
                            kind="trade",
                            event_time=int(row["T"]),
                            price=float(row["p"]),
                            amount=float(row["v"]),
                        )
