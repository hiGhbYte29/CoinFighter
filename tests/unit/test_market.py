from time import monotonic

import pytest

from app.modules.market.normalizer import normalize_symbol
from app.modules.market.service import MarketService


@pytest.mark.parametrize(
    ("source", "expected"),
    [("btc-usdt", "BTC/USDT"), ("ETH_USDT", "ETH/USDT"), ("solusdt", "SOL/USDT")],
)
def test_normalize_symbol(source: str, expected: str) -> None:
    assert normalize_symbol(source) == expected


class FakeMarketProvider:
    async def get_tickers(self, quote: str = "USDT") -> list[dict]:
        return [
            {
                "provider": "binance",
                "symbol": f"C{index}/USDT",
                "base": f"C{index}",
                "quote": quote,
                "last": float(index),
                "change_percent": float(index - 12),
                "base_volume": 10.0,
                "quote_volume": float(index * 100),
            }
            for index in range(1, 26)
        ]


class FakeRegistry:
    def get(self, provider: str, market_type: str) -> FakeMarketProvider:
        return FakeMarketProvider()


async def test_market_list_is_ranked_and_paginated() -> None:
    service = MarketService(FakeRegistry())  # type: ignore[arg-type]
    service._coin_market_cache = (
        monotonic(),
        [
            {
                "symbol": f"c{index}",
                "name": f"Coin {index}",
                "image": None,
                "market_cap": float(index * 1_000_000),
                "market_cap_rank": 26 - index,
            }
            for index in range(1, 26)
        ],
    )

    first_page = await service.get_markets("binance", "spot", 1, 20, "market_cap", "desc")
    second_page = await service.get_markets("binance", "spot", 2, 20, "market_cap", "desc")

    assert first_page.total == 25
    assert first_page.pages == 2
    assert len(first_page.items) == 20
    assert len(second_page.items) == 5
    assert first_page.items[0].base == "C25"
    assert second_page.items[-1].base == "C1"
