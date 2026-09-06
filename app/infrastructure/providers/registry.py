from app.core.config import Settings
from app.infrastructure.providers.base import MarketDataProvider
from app.infrastructure.providers.ccxt_provider import CcxtProvider


class ProviderRegistry:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._providers: dict[tuple[str, str], MarketDataProvider] = {}

    def get(self, provider_id: str, market_type: str = "spot") -> MarketDataProvider:
        key = (provider_id.lower(), market_type.lower())
        if key not in self._providers:
            provider: MarketDataProvider = CcxtProvider(
                key[0],
                key[1],
                enable_rate_limit=self.settings.ccxt_enable_rate_limit,
                timeout_seconds=self.settings.http_timeout_seconds,
            )
            self._providers[key] = provider
        return self._providers[key]

    async def close(self) -> None:
        for provider in self._providers.values():
            await provider.close()
        self._providers.clear()
