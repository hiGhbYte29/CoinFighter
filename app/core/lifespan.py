from collections.abc import AsyncIterator
from concurrent.futures import ProcessPoolExecutor
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.core.config import get_settings
from app.infrastructure.providers.market_stream import MarketStreamService
from app.infrastructure.providers.registry import ProviderRegistry
from app.infrastructure.runtime.task_registry import TaskRegistry
from app.infrastructure.storage.json_store import JsonStore
from app.infrastructure.storage.parquet import ParquetStorage
from app.infrastructure.storage.paths import StoragePaths
from app.modules.backtest.runner import BacktestService
from app.modules.datasets.catalog import DatasetCatalog
from app.modules.datasets.service import DatasetService
from app.modules.indicators.service import IndicatorService
from app.modules.market.service import MarketService
from app.modules.strategies.loader import StrategyLoader


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    paths = StoragePaths(settings.local_data_dir)
    json_store = JsonStore()
    parquet = ParquetStorage(paths, settings.parquet_compression)
    providers = ProviderRegistry(settings)
    tasks = TaskRegistry(paths.tasks, json_store)
    catalog = DatasetCatalog(paths.catalog / "datasets.json", json_store)
    strategy_loader = StrategyLoader(settings.strategy_dir, settings.example_strategy_dir)
    pool = ProcessPoolExecutor(max_workers=settings.max_backtest_processes)

    app.state.settings = settings
    app.state.market_service = MarketService(providers)
    app.state.market_stream_service = MarketStreamService()
    app.state.indicator_service = IndicatorService()
    app.state.dataset_service = DatasetService(
        providers,
        parquet,
        paths,
        catalog,
        tasks,
        settings.max_download_tasks,
    )
    app.state.strategy_loader = strategy_loader
    app.state.backtest_service = BacktestService(
        pool,
        tasks,
        paths,
        json_store,
        parquet,
        strategy_dir=settings.strategy_dir,
        example_strategy_dir=settings.example_strategy_dir,
        timeout_seconds=settings.backtest_timeout_seconds,
    )
    try:
        yield
    finally:
        await providers.close()
        pool.shutdown(wait=False, cancel_futures=True)
