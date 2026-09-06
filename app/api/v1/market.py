from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Query, WebSocket, WebSocketDisconnect

from app.api.dependencies import get_market_service
from app.modules.market.schemas import Candle, MarketPage, OrderBook, Ticker
from app.modules.market.service import MarketService
from app.modules.market.subscriptions import MarketSubscription

router = APIRouter()
MarketDep = Annotated[MarketService, Depends(get_market_service)]


@router.get("/providers")
async def providers(service: MarketDep) -> list[dict[str, str]]:
    """查询支持的行情交易所列表。"""
    return service.list_providers()


@router.get("/symbols")
async def symbols(
    service: MarketDep,
    provider: str = "binance",
    market_type: str = "spot",
) -> list[str]:
    """查询指定交易所支持的交易对。"""
    return await service.get_symbols(provider, market_type)


@router.get("/ticker", response_model=Ticker)
async def ticker(
    service: MarketDep,
    symbol: str = "BTC/USDT",
    provider: str = "binance",
    market_type: str = "spot",
) -> Ticker:
    """查询指定交易对的最新行情。"""
    return await service.get_ticker(provider, market_type, symbol)


@router.get("/markets", response_model=MarketPage)
async def markets(
    service: MarketDep,
    provider: str = "binance",
    market_type: str = "spot",
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    sort_by: Literal["market_cap", "quote_volume", "change", "price"] = "market_cap",
    sort_order: Literal["asc", "desc"] = "desc",
) -> MarketPage:
    """分页查询交易所现货行情列表。"""
    return await service.get_markets(
        provider, market_type, page, page_size, sort_by, sort_order
    )


@router.get("/order-book", response_model=OrderBook)
async def order_book(
    service: MarketDep,
    symbol: str = "BTC/USDT",
    limit: int = Query(default=20, ge=1, le=100),
    provider: str = "binance",
    market_type: str = "spot",
) -> OrderBook:
    """查询详情页指定交易对的订单簿。"""
    return await service.get_order_book(provider, market_type, symbol, limit)


@router.get("/candles", response_model=list[Candle])
async def candles(
    service: MarketDep,
    symbol: str = "BTC/USDT",
    timeframe: str = Query(default="1h", pattern=r"^\d+[mhdw]$"),
    limit: int = Query(default=200, ge=1, le=1000),
    provider: str = "binance",
    market_type: str = "spot",
) -> list[Candle]:
    """查询指定交易对的历史 K 线。"""
    return await service.get_candles(provider, market_type, symbol, timeframe, limit)


@router.websocket("/ws")
async def market_socket(
    websocket: WebSocket,
    provider: str = "binance",
    market_type: str = "spot",
    symbol: str = "BTC/USDT",
) -> None:
    """通过 WebSocket 持续推送指定交易对行情。"""
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
