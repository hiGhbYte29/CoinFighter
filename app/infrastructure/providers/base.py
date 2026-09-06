from typing import Protocol


class MarketDataProvider(Protocol):
    id: str
    market_type: str

    async def get_symbols(self) -> list[str]: ...

    async def get_ticker(self, symbol: str) -> dict: ...

    async def get_tickers(self, quote: str = "USDT") -> list[dict]: ...

    async def get_order_book(self, symbol: str, limit: int = 20) -> dict: ...

    async def get_candles(
        self,
        symbol: str,
        timeframe: str,
        since_ms: int | None = None,
        limit: int = 500,
    ) -> list[dict]: ...

    async def close(self) -> None: ...
