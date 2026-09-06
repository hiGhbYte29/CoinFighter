import asyncio
from collections.abc import AsyncIterator

from app.modules.market.schemas import Ticker
from app.modules.market.service import MarketService


class MarketSubscription:
    """REST-polling stream used by the local MVP WebSocket endpoint."""

    def __init__(self, market: MarketService, interval_seconds: float = 2.0) -> None:
        self.market = market
        self.interval_seconds = interval_seconds

    async def ticker_stream(
        self, provider: str, market_type: str, symbol: str
    ) -> AsyncIterator[Ticker]:
        while True:
            yield await self.market.get_ticker(provider, market_type, symbol)
            await asyncio.sleep(self.interval_seconds)
