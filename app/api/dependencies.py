from fastapi import Request

from app.infrastructure.providers.market_stream import MarketStreamService
from app.modules.backtest.runner import BacktestService
from app.modules.datasets.service import DatasetService
from app.modules.indicators.service import IndicatorService
from app.modules.market.service import MarketService
from app.modules.strategies.loader import StrategyLoader


async def get_market_service(request: Request) -> MarketService:
    return request.app.state.market_service


async def get_indicator_service(request: Request) -> IndicatorService:
    return request.app.state.indicator_service


async def get_market_stream_service(request: Request) -> MarketStreamService:
    return request.app.state.market_stream_service


async def get_dataset_service(request: Request) -> DatasetService:
    return request.app.state.dataset_service


async def get_strategy_loader(request: Request) -> StrategyLoader:
    return request.app.state.strategy_loader


async def get_backtest_service(request: Request) -> BacktestService:
    return request.app.state.backtest_service
