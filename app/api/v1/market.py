from time import monotonic
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Query, WebSocket, WebSocketDisconnect
from pydantic import ValidationError

from app.api.dependencies import get_indicator_service, get_market_service
from app.core.exceptions import AppError
from app.infrastructure.providers.market_stream import MarketStreamEvent, MarketStreamService
from app.modules.indicators.schemas import ChartDataRequest, ChartDataResponse
from app.modules.indicators.service import IndicatorService
from app.modules.market.schemas import Candle, MarketPage, OrderBook, Ticker
from app.modules.market.service import MarketService
from app.modules.market.subscriptions import MarketSubscription
from app.modules.market.timeframes import timeframe_milliseconds

router = APIRouter()
MarketDep = Annotated[MarketService, Depends(get_market_service)]
IndicatorDep = Annotated[IndicatorService, Depends(get_indicator_service)]


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
    return await service.get_markets(provider, market_type, page, page_size, sort_by, sort_order)


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


@router.post("/chart-data", response_model=ChartDataResponse)
async def chart_data(
    request: ChartDataRequest,
    market_service: MarketDep,
    indicator_service: IndicatorDep,
) -> ChartDataResponse:
    """查询带有预热历史的 K 线并用统一 Python 指标内核计算图表数据。"""
    candles = await _load_chart_candles(request, market_service, indicator_service)
    return _chart_response(request, candles, indicator_service)


async def _load_chart_candles(
    request: ChartDataRequest,
    market_service: MarketService,
    indicator_service: IndicatorService,
) -> list[Candle]:
    history = indicator_service.required_history(request.indicators)
    fetch_limit = min(1000, request.visible_limit + history)
    return await market_service.get_candles(
        request.provider,
        request.market_type,
        request.symbol,
        request.timeframe,
        fetch_limit,
    )


def _chart_response(
    request: ChartDataRequest,
    candles: list[Candle],
    indicator_service: IndicatorService,
) -> ChartDataResponse:
    calculated = indicator_service.calculate(candles, request.indicators)
    visible_candles = candles[-request.visible_limit :]
    visible_indicators = [
        output.model_copy(
            update={
                "plots": [
                    plot.model_copy(update={"values": plot.values[-request.visible_limit :]})
                    for plot in output.plots
                ]
            }
        )
        for output in calculated
    ]
    return ChartDataResponse(candles=visible_candles, indicators=visible_indicators)


def _merge_stream_event(
    candles: list[Candle], event: MarketStreamEvent, timeframe: str
) -> float | None:
    if event.kind == "candle" and event.candle is not None:
        incoming = event.candle
        for index in range(len(candles) - 1, max(-1, len(candles) - 4), -1):
            if candles[index].timestamp == incoming.timestamp:
                candles[index] = incoming
                return incoming.close
        if not candles or incoming.timestamp > candles[-1].timestamp:
            if candles:
                candles[-1] = candles[-1].model_copy(update={"is_closed": True})
            candles.append(incoming)
            return incoming.close
        return None
    if event.kind != "trade" or event.price is None:
        return None
    interval = timeframe_milliseconds(timeframe)
    timestamp = event.event_time // interval * interval
    if not candles or timestamp > candles[-1].timestamp:
        if candles:
            candles[-1] = candles[-1].model_copy(update={"is_closed": True})
        amount = event.amount or 0.0
        candles.append(
            Candle(
                timestamp=timestamp,
                open=event.price,
                high=event.price,
                low=event.price,
                close=event.price,
                volume=amount,
                is_closed=False,
            )
        )
        return event.price
    if timestamp == candles[-1].timestamp:
        current = candles[-1]
        candles[-1] = current.model_copy(
            update={
                "high": max(current.high, event.price),
                "low": min(current.low, event.price),
                "close": event.price,
                "volume": current.volume + max(0.0, event.amount or 0.0),
                "is_closed": False,
            }
        )
        return event.price
    return None


@router.websocket("/chart/ws")
async def chart_socket(websocket: WebSocket) -> None:
    """推送实时 K 线快照，并根据客户端选择实时重算技术指标。"""
    await websocket.accept()
    market_service: MarketService = websocket.app.state.market_service
    indicator_service: IndicatorService = websocket.app.state.indicator_service
    stream_service: MarketStreamService = websocket.app.state.market_stream_service
    try:
        payload = await websocket.receive_json()
        request = ChartDataRequest.model_validate(payload)
        candles = await _load_chart_candles(request, market_service, indicator_service)
        fetch_limit = min(
            1000,
            request.visible_limit + indicator_service.required_history(request.indicators),
        )
        sequence = 0
        snapshot = _chart_response(request, candles, indicator_service)
        await websocket.send_json(
            {
                "type": "snapshot",
                "sequence": sequence,
                "last_price": candles[-1].close if candles else None,
                "data": snapshot.model_dump(mode="json"),
            }
        )
        last_sent = monotonic()
        async for event in stream_service.stream(
            request.provider, request.market_type, request.symbol, request.timeframe
        ):
            last_price = _merge_stream_event(candles, event, request.timeframe)
            if last_price is None:
                continue
            if len(candles) > fetch_limit:
                del candles[:-fetch_limit]
            now = monotonic()
            if now - last_sent < 0.2:
                continue
            sequence += 1
            update = _chart_response(request, candles, indicator_service)
            await websocket.send_json(
                {
                    "type": "update",
                    "sequence": sequence,
                    "last_price": last_price,
                    "data": update.model_dump(mode="json"),
                }
            )
            last_sent = now
    except WebSocketDisconnect:
        return
    except (ValidationError, AppError, ValueError) as error:
        message = error.message if isinstance(error, AppError) else str(error)
        await websocket.send_json({"type": "error", "message": message})
        await websocket.close(code=1008)
    except Exception as error:
        await websocket.send_json({"type": "error", "message": str(error)})
        await websocket.close(code=1011)


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
