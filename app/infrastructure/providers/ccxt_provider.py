import re
from typing import Any

from app.core.exceptions import AppError


class CcxtProvider:
    def __init__(
        self,
        exchange_id: str,
        market_type: str = "spot",
        *,
        enable_rate_limit: bool = True,
        timeout_seconds: float = 30,
    ) -> None:
        if not re.fullmatch(r"[a-z0-9_]+", exchange_id):
            raise AppError("PROVIDER_INVALID", "行情提供方名称无效")
        self.id = exchange_id
        self.market_type = market_type
        self._enable_rate_limit = enable_rate_limit
        self._timeout_ms = int(timeout_seconds * 1000)
        self._exchange: Any | None = None

    async def _client(self) -> Any:
        if self._exchange is not None:
            return self._exchange
        try:
            import ccxt.async_support as ccxt
        except ImportError as error:
            raise AppError(
                "PROVIDER_DEPENDENCY_MISSING",
                "未安装 CCXT，无法连接真实行情源",
                status_code=503,
            ) from error
        exchange_class = getattr(ccxt, self.id, None)
        if exchange_class is None:
            raise AppError("PROVIDER_NOT_FOUND", f"CCXT 不支持行情源 {self.id}", status_code=404)
        self._exchange = exchange_class(
            {
                "enableRateLimit": self._enable_rate_limit,
                "timeout": self._timeout_ms,
                "options": {"defaultType": self.market_type},
            }
        )
        return self._exchange

    async def _loaded_client(self) -> Any:
        exchange = await self._client()
        if not exchange.markets:
            try:
                await exchange.load_markets()
            except Exception as error:
                raise AppError(
                    "PROVIDER_UNAVAILABLE",
                    f"无法连接行情源 {self.id}",
                    status_code=503,
                    details={"reason": str(error)},
                ) from error
        return exchange

    async def get_symbols(self) -> list[str]:
        exchange = await self._loaded_client()
        symbols = []
        for symbol, market in exchange.markets.items():
            if market.get("active") is False:
                continue
            if self.market_type == "spot" and not market.get("spot", False):
                continue
            symbols.append(symbol)
        return sorted(symbols)

    async def get_ticker(self, symbol: str) -> dict:
        exchange = await self._loaded_client()
        try:
            ticker = await exchange.fetch_ticker(symbol)
        except Exception as error:
            raise AppError(
                "PROVIDER_REQUEST_FAILED",
                f"获取 {symbol} 行情失败",
                status_code=502,
                details={"reason": str(error)},
            ) from error
        open_price = ticker.get("open")
        last = ticker.get("last")
        percentage = ticker.get("percentage")
        if percentage is None and open_price and last:
            percentage = (last / open_price - 1) * 100
        return {
            "provider": self.id,
            "market_type": self.market_type,
            "symbol": symbol,
            "timestamp": ticker.get("timestamp"),
            "last": last,
            "open": open_price,
            "high": ticker.get("high"),
            "low": ticker.get("low"),
            "change_percent": percentage,
            "base_volume": ticker.get("baseVolume"),
        }

    async def get_candles(
        self,
        symbol: str,
        timeframe: str,
        since_ms: int | None = None,
        limit: int = 500,
    ) -> list[dict]:
        exchange = await self._loaded_client()
        if not exchange.has.get("fetchOHLCV"):
            raise AppError(
                "PROVIDER_METHOD_UNSUPPORTED",
                f"{self.id} 不支持 K 线下载",
                status_code=422,
            )
        try:
            rows = await exchange.fetch_ohlcv(symbol, timeframe, since_ms, limit)
        except Exception as error:
            raise AppError(
                "PROVIDER_REQUEST_FAILED",
                f"下载 {symbol} K 线失败",
                status_code=502,
                details={"reason": str(error)},
            ) from error
        now_ms = exchange.milliseconds()
        timeframe_ms = exchange.parse_timeframe(timeframe) * 1000
        return [
            {
                "timestamp": int(row[0]),
                "open": float(row[1]),
                "high": float(row[2]),
                "low": float(row[3]),
                "close": float(row[4]),
                "volume": float(row[5]),
                "is_closed": int(row[0]) + timeframe_ms <= now_ms,
            }
            for row in rows
        ]

    async def close(self) -> None:
        if self._exchange is not None:
            await self._exchange.close()
            self._exchange = None
