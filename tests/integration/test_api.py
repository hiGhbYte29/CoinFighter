from pathlib import Path

from httpx import ASGITransport, AsyncClient

from app.core.config import get_settings
from app.main import create_app
from app.modules.market.schemas import Candle


async def test_local_service_and_strategy_endpoints(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("LOCAL_DATA_DIR", str(tmp_path / "data"))
    get_settings.cache_clear()
    try:
        app = create_app()
        transport = ASGITransport(app=app)
        async with app.router.lifespan_context(app):
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                assert (await client.get("/api/v1/health/live")).json() == {"status": "ok"}
                providers = await client.get("/api/v1/market/providers")
                assert providers.status_code == 200
                assert [item["id"] for item in providers.json()] == [
                    "binance",
                    "okx",
                    "bybit",
                ]
                indicator_catalog = await client.get("/api/v1/indicators/catalog")
                assert indicator_catalog.status_code == 200
                assert {item["id"] for item in indicator_catalog.json()["items"]} >= {
                    "ma",
                    "macd",
                    "rsi",
                }
                invalid_page_size = await client.get("/api/v1/market/markets?page_size=101")
                assert invalid_page_size.status_code == 422
                assert (await client.get("/api/v1/health/ready")).json()["provider"] == "binance"
                strategies = await client.get("/api/v1/strategies")
                assert strategies.status_code == 200
                assert {item["name"] for item in strategies.json()} >= {
                    "buy_and_hold",
                    "sma_cross",
                    "macd_cross",
                }

                class FakeChartMarket:
                    async def get_candles(
                        self,
                        provider: str,
                        market_type: str,
                        symbol: str,
                        timeframe: str,
                        limit: int,
                    ) -> list[Candle]:
                        return [
                            Candle(
                                timestamp=1_700_000_000_000 + index * 60_000,
                                open=100 + index,
                                high=102 + index,
                                low=99 + index,
                                close=101 + index,
                                volume=10 + index,
                                is_closed=index < limit - 1,
                            )
                            for index in range(limit)
                        ]

                app.state.market_service = FakeChartMarket()
                chart = await client.post(
                    "/api/v1/market/chart-data",
                    json={
                        "visible_limit": 50,
                        "indicators": [
                            {
                                "instance_id": "ma-default",
                                "indicator_id": "ma",
                                "placement": "main",
                                "parameters": {"periods": [7, 25]},
                            }
                        ],
                    },
                )
                assert chart.status_code == 200
                assert len(chart.json()["candles"]) == 50
                assert len(chart.json()["indicators"][0]["plots"]) == 2
    finally:
        get_settings.cache_clear()
