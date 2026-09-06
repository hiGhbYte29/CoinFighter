from __future__ import annotations

import asyncio
from datetime import datetime
from pathlib import Path

from app.core.exceptions import AppError
from app.infrastructure.providers.registry import ProviderRegistry
from app.infrastructure.runtime.task_registry import TaskRegistry
from app.infrastructure.storage.parquet import ParquetStorage
from app.infrastructure.storage.paths import StoragePaths, safe_segment
from app.modules.datasets.catalog import DatasetCatalog, build_metadata
from app.modules.datasets.downloader import download_candles
from app.modules.datasets.schemas import DatasetDownloadRequest, DatasetMetadata, DatasetValidation
from app.modules.datasets.validator import validate_candles
from app.modules.market.normalizer import normalize_symbol
from app.modules.market.timeframes import timeframe_milliseconds


def dataset_id_for(provider: str, market_type: str, symbol: str, timeframe: str) -> str:
    return "_".join(
        (
            safe_segment(provider.lower()),
            safe_segment(market_type.lower()),
            safe_segment(symbol.lower()),
            safe_segment(timeframe),
        )
    )


class DatasetService:
    def __init__(
        self,
        providers: ProviderRegistry,
        storage: ParquetStorage,
        paths: StoragePaths,
        catalog: DatasetCatalog,
        tasks: TaskRegistry,
        max_concurrency: int = 2,
    ) -> None:
        self.providers = providers
        self.storage = storage
        self.paths = paths
        self.catalog = catalog
        self.tasks = tasks
        self._semaphore = asyncio.Semaphore(max_concurrency)
        self._running: set[asyncio.Task] = set()

    def list(self) -> list[DatasetMetadata]:
        return self.catalog.list()

    def get(self, dataset_id: str) -> DatasetMetadata:
        return self.catalog.get(dataset_id)

    def candles(
        self,
        dataset_id: str,
        *,
        start: datetime | None = None,
        end: datetime | None = None,
        limit: int | None = None,
    ) -> list[dict]:
        dataset = self.catalog.get(dataset_id)
        return self.storage.read_candles(
            Path(dataset.path),
            start_ms=int(start.timestamp() * 1000) if start else None,
            end_ms=int(end.timestamp() * 1000) if end else None,
            limit=limit,
        )

    async def start_download(self, request: DatasetDownloadRequest) -> dict:
        request.symbol = normalize_symbol(request.symbol)
        task = await self.tasks.create("download", request.model_dump(mode="json"))
        future = asyncio.create_task(self._run_download(task["task_id"], request))
        self._running.add(future)
        future.add_done_callback(self._running.discard)
        return task

    async def _run_download(self, task_id: str, request: DatasetDownloadRequest) -> None:
        async with self._semaphore:
            await self.tasks.update(task_id, status="RUNNING", progress=1, message="正在准备下载")
            try:
                provider = self.providers.get(request.provider, request.market_type)
                start_ms = int(request.start.timestamp() * 1000)
                end_ms = int(request.end.timestamp() * 1000)
                existing = self.catalog.find(
                    request.provider, request.market_type, request.symbol, request.timeframe
                )
                step = timeframe_milliseconds(request.timeframe)
                ranges: list[tuple[int, int]] = []
                if existing is None:
                    ranges.append((start_ms, end_ms))
                else:
                    existing_start = int(existing.start.timestamp() * 1000)
                    existing_end = int(existing.end.timestamp() * 1000)
                    if start_ms < existing_start:
                        ranges.append((start_ms, min(end_ms, existing_start)))
                    if end_ms > existing_end + step:
                        ranges.append((max(start_ms, existing_end + step), end_ms))

                downloaded: list[dict] = []

                async def progress(value: int, message: str) -> None:
                    await self.tasks.update(task_id, progress=value, message=message)

                for range_start, range_end in ranges:
                    downloaded.extend(
                        await download_candles(
                            provider,
                            request.symbol,
                            request.timeframe,
                            range_start,
                            range_end,
                            progress,
                        )
                    )

                directory = self.paths.dataset_dir(
                    request.provider, request.market_type, request.symbol, request.timeframe
                )
                if downloaded:
                    await asyncio.to_thread(
                        self.storage.merge_candles,
                        request.provider,
                        request.market_type,
                        request.symbol,
                        request.timeframe,
                        downloaded,
                    )
                rows = await asyncio.to_thread(self.storage.read_candles, directory)
                if not rows:
                    raise AppError("DATASET_EMPTY", "行情源没有返回指定范围的数据")
                identifier = dataset_id_for(
                    request.provider, request.market_type, request.symbol, request.timeframe
                )
                metadata = build_metadata(
                    dataset_id=identifier,
                    provider=request.provider,
                    market_type=request.market_type,
                    symbol=request.symbol,
                    timeframe=request.timeframe,
                    rows=rows,
                    path=directory,
                )
                self.catalog.upsert(metadata)
                await self.tasks.update(
                    task_id,
                    status="COMPLETED",
                    progress=100,
                    message="数据下载完成",
                    result=metadata.model_dump(mode="json"),
                )
            except Exception as error:
                await self.tasks.update(
                    task_id,
                    status="FAILED",
                    message=str(error),
                    error={"type": type(error).__name__, "message": str(error)},
                )

    def validate(self, dataset_id: str) -> DatasetValidation:
        dataset = self.catalog.get(dataset_id)
        rows = self.storage.read_candles(Path(dataset.path))
        return validate_candles(dataset_id, rows, dataset.timeframe)
