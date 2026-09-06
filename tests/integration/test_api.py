from pathlib import Path

from httpx import ASGITransport, AsyncClient

from app.core.config import get_settings
from app.main import create_app


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
    finally:
        get_settings.cache_clear()
