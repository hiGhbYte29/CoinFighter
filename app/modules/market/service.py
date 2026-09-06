import asyncio
import logging
import math
from time import monotonic
from typing import Any, Literal

import httpx

from app.infrastructure.providers.registry import ProviderRegistry
from app.modules.market.normalizer import normalize_symbol
from app.modules.market.schemas import Candle, MarketPage, MarketSummary, OrderBook, Ticker

logger = logging.getLogger(__name__)

SortField = Literal["market_cap", "quote_volume", "change", "price"]
SortOrder = Literal["asc", "desc"]


class MarketService:
    def __init__(self, providers: ProviderRegistry) -> None:
        self.providers = providers
        self._coin_market_cache: tuple[float, list[dict[str, Any]]] | None = None
        self._coin_market_lock = asyncio.Lock()

    def list_providers(self) -> list[dict[str, str]]:
        return [
            {"id": "binance", "name": "Binance", "mode": "ccxt"},
            {"id": "okx", "name": "OKX", "mode": "ccxt"},
            {"id": "bybit", "name": "Bybit", "mode": "ccxt"},
        ]

    async def get_symbols(self, provider: str, market_type: str) -> list[str]:
        return await self.providers.get(provider, market_type).get_symbols()

    async def get_ticker(self, provider: str, market_type: str, symbol: str) -> Ticker:
        normalized = normalize_symbol(symbol)
        result = await self.providers.get(provider, market_type).get_ticker(normalized)
        return Ticker.model_validate(result)

    async def get_markets(
        self,
        provider: str,
        market_type: str,
        page: int,
        page_size: int,
        sort_by: SortField,
        sort_order: SortOrder,
    ) -> MarketPage:
        rows = await self.providers.get(provider, market_type).get_tickers("USDT")
        coin_rows = await self._get_coin_market_data()
        coin_by_symbol: dict[str, dict[str, Any]] = {}
        for coin in coin_rows:
            symbol = str(coin.get("symbol") or "").upper()
            if symbol and symbol not in coin_by_symbol:
                coin_by_symbol[symbol] = coin

        items: list[MarketSummary] = []
        for row in rows:
            base = str(row.get("base") or "").upper()
            coin = coin_by_symbol.get(base, {})
            items.append(
                MarketSummary(
                    **row,
                    name=str(coin.get("name") or base),
                    image_url=coin.get("image"),
                    market_cap=coin.get("market_cap"),
                    market_cap_rank=coin.get("market_cap_rank"),
                )
            )

        value_getters = {
            "market_cap": lambda item: item.market_cap,
            "quote_volume": lambda item: item.quote_volume,
            "change": lambda item: item.change_percent,
            "price": lambda item: item.last,
        }
        getter = value_getters[sort_by]
        populated = [item for item in items if getter(item) is not None]
        missing = [item for item in items if getter(item) is None]
        populated.sort(key=lambda item: float(getter(item) or 0), reverse=sort_order == "desc")
        if sort_by == "market_cap":
            missing.sort(key=lambda item: float(item.quote_volume or 0), reverse=True)
        else:
            missing.sort(key=lambda item: item.symbol)
        items = populated + missing

        total = len(items)
        pages = max(1, math.ceil(total / page_size))
        start = (page - 1) * page_size
        return MarketPage(
            provider=provider.lower(),
            page=page,
            page_size=page_size,
            total=total,
            pages=pages,
            sort_by=sort_by,
            sort_order=sort_order,
            items=items[start : start + page_size],
        )

    async def get_order_book(
        self, provider: str, market_type: str, symbol: str, limit: int
    ) -> OrderBook:
        normalized = normalize_symbol(symbol)
        result = await self.providers.get(provider, market_type).get_order_book(normalized, limit)
        return OrderBook.model_validate(result)

    async def get_candles(
        self,
        provider: str,
        market_type: str,
        symbol: str,
        timeframe: str,
        limit: int,
    ) -> list[Candle]:
        normalized = normalize_symbol(symbol)
        rows = await self.providers.get(provider, market_type).get_candles(
            normalized, timeframe, limit=limit
        )
        return [Candle.model_validate(row) for row in rows]

    async def _get_coin_market_data(self) -> list[dict[str, Any]]:
        now = monotonic()
        if self._coin_market_cache and now - self._coin_market_cache[0] < 60:
            return self._coin_market_cache[1]
        async with self._coin_market_lock:
            now = monotonic()
            if self._coin_market_cache and now - self._coin_market_cache[0] < 60:
                return self._coin_market_cache[1]
            try:
                async with httpx.AsyncClient(timeout=8.0) as client:
                    response = await client.get(
                        "https://api.coingecko.com/api/v3/coins/markets",
                        params={
                            "vs_currency": "usd",
                            "order": "market_cap_desc",
                            "per_page": 250,
                            "page": 1,
                            "sparkline": "false",
                        },
                    )
                    response.raise_for_status()
                    data = response.json()
                    if not isinstance(data, list):
                        raise ValueError("CoinGecko 返回了非列表数据")
            except (httpx.HTTPError, ValueError) as error:
                logger.warning("无法获取市值数据，将按交易所成交额回退排序: %s", error)
                return self._coin_market_cache[1] if self._coin_market_cache else []
            self._coin_market_cache = (now, data)
            return data
