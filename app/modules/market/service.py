from app.infrastructure.providers.registry import ProviderRegistry
from app.modules.market.normalizer import normalize_symbol
from app.modules.market.schemas import Candle, Ticker


class MarketService:
    def __init__(self, providers: ProviderRegistry) -> None:
        self.providers = providers

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
