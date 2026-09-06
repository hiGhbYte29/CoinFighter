from typing import Annotated

from fastapi import APIRouter, Depends, Query, WebSocket, WebSocketDisconnect

from app.api.dependencies import get_market_service
from app.modules.market.schemas import Candle, Ticker
from app.modules.market.service import MarketService
from app.modules.market.subscriptions import MarketSubscription

router = APIRouter()
MarketDep = Annotated[MarketService, Depends(get_market_service)]


@router.get("/providers")
async def providers(service: MarketDep) -> list[dict[str, str]]:
    return service.list_providers()


@router.get("/symbols")
async def symbols(
    service: MarketDep,
    provider: str = "binance",
    market_type: str = "spot",
) -> list[str]:
    return await service.get_symbols(provider, market_type)


@router.get("/ticker", response_model=Ticker)
async def ticker(
    service: MarketDep,
    symbol: str = "BTC/USDT",
    provider: str = "binance",
    market_type: str = "spot",
) -> Ticker:
    return await service.get_ticker(provider, market_type, symbol)


@router.get("/candles", response_model=list[Candle])
async def candles(
    service: MarketDep,
    symbol: str = "BTC/USDT",
    timeframe: str = Query(default="1h", pattern=r"^\d+[mhdw]$"),
    limit: int = Query(default=200, ge=1, le=1000),
    provider: str = "binance",
    market_type: str = "spot",
) -> list[Candle]:
    return await service.get_candles(provider, market_type, symbol, timeframe, limit)


@router.websocket("/ws")
async def market_socket(
    websocket: WebSocket,
    provider: str = "binance",
    market_type: str = "spot",
    symbol: str = "BTC/USDT",
) -> None:
    await websocket.accept()
    service: MarketService = websocket.app.state.market_service
    subscription = MarketSubscription(service)
    try:
        async for update in subscription.ticker_stream(provider, market_type, symbol):
            await websocket.send_json(update.model_dump(mode="json"))
    except WebSocketDisconnect:
        return
    except Exception as error:
        await websocket.send_json({"type": "error", "message": str(error)})
        await websocket.close(code=1011)
