from fastapi import Request

from app.modules.backtest.runner import BacktestService
from app.modules.datasets.service import DatasetService
from app.modules.market.service import MarketService
from app.modules.strategies.loader import StrategyLoader


async def get_market_service(request: Request) -> MarketService:
    return request.app.state.market_service


async def get_dataset_service(request: Request) -> DatasetService:
    return request.app.state.dataset_service


async def get_strategy_loader(request: Request) -> StrategyLoader:
    return request.app.state.strategy_loader


async def get_backtest_service(request: Request) -> BacktestService:
    return request.app.state.backtest_service
