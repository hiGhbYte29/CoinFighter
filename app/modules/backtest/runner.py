from __future__ import annotations

import asyncio
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from typing import Any

from app.core.exceptions import AppError
from app.infrastructure.runtime.task_registry import TaskRegistry
from app.infrastructure.storage.json_store import JsonStore
from app.infrastructure.storage.parquet import ParquetStorage
from app.infrastructure.storage.paths import StoragePaths
from app.modules.backtest.engine import run_engine
from app.modules.backtest.reports import write_report
from app.modules.backtest.schemas import BacktestRequest
from app.modules.datasets.catalog import DatasetCatalog
from app.modules.strategies.loader import StrategyLoader


def execute_backtest_job(payload: dict[str, Any]) -> dict:
    paths = StoragePaths(Path(payload["local_data_dir"]))
    json_store = JsonStore()
    parquet = ParquetStorage(paths, payload["parquet_compression"])
    catalog = DatasetCatalog(paths.catalog / "datasets.json", json_store)
    dataset = catalog.get(payload["request"]["dataset_id"])
    rows = parquet.read_candles(Path(dataset.path))
    loader = StrategyLoader(Path(payload["strategy_dir"]), Path(payload["example_strategy_dir"]))
    strategy_class = loader.load_class(payload["request"]["strategy"])
    result = run_engine(
        rows,
        strategy_class,
        payload["request"].get("parameters", {}),
        initial_cash=float(payload["request"]["initial_cash"]),
        fee_rate=float(payload["request"]["fee_rate"]),
        slippage=float(payload["request"]["slippage"]),
        timeframe=dataset.timeframe,
    )
    result["dataset"] = dataset.model_dump(mode="json")
    result["strategy"] = payload["request"]["strategy"]
    write_report(paths.backtest_dir(payload["run_id"]), result, json_store, parquet)
    return {
        "metrics": result["metrics"],
        "dataset": result["dataset"],
        "strategy": result["strategy"],
    }


class BacktestService:
    def __init__(
        self,
        pool: ProcessPoolExecutor,
        tasks: TaskRegistry,
        paths: StoragePaths,
        json_store: JsonStore,
        parquet: ParquetStorage,
        *,
        strategy_dir: Path,
        example_strategy_dir: Path,
        timeout_seconds: int,
    ) -> None:
        self.pool = pool
        self.tasks = tasks
        self.paths = paths
        self.json_store = json_store
        self.parquet = parquet
        self.strategy_dir = strategy_dir
        self.example_strategy_dir = example_strategy_dir
        self.timeout_seconds = timeout_seconds
        self._futures: dict[str, asyncio.Task] = {}

    @staticmethod
    def _as_summary(task: dict) -> dict:
        return {**task, "run_id": task["task_id"]}

    async def start(self, request: BacktestRequest) -> dict:
        task = await self.tasks.create("bt", request.model_dump(mode="json"))
        run_id = task["task_id"]
        directory = self.paths.backtest_dir(run_id)
        directory.mkdir(parents=True, exist_ok=True)
        self.json_store.write(directory / "request.json", request.model_dump(mode="json"))
        self.json_store.write(directory / "status.json", self._as_summary(task))
        future = asyncio.create_task(self._run(run_id, request))
        self._futures[run_id] = future
        future.add_done_callback(lambda _: self._futures.pop(run_id, None))
        return self._as_summary(task)

    async def _update(self, run_id: str, **changes: Any) -> dict:
        task = await self.tasks.update(run_id, **changes)
        self.json_store.write(
            self.paths.backtest_dir(run_id) / "status.json", self._as_summary(task)
        )
        return task

    async def _run(self, run_id: str, request: BacktestRequest) -> None:
        await self._update(run_id, status="RUNNING", progress=10, message="正在运行回测")
        payload = {
            "run_id": run_id,
            "request": request.model_dump(mode="json"),
            "local_data_dir": str(self.paths.root),
            "strategy_dir": str(self.strategy_dir),
            "example_strategy_dir": str(self.example_strategy_dir),
            "parquet_compression": self.parquet.compression,
        }
        loop = asyncio.get_running_loop()
        try:
            result = await asyncio.wait_for(
                loop.run_in_executor(self.pool, execute_backtest_job, payload),
                timeout=self.timeout_seconds,
            )
            await self._update(
                run_id,
                status="COMPLETED",
                progress=100,
                message="回测完成",
                result=result,
            )
        except asyncio.CancelledError:
            await self._update(run_id, status="CANCELED", message="回测已取消")
        except TimeoutError:
            await self._update(run_id, status="FAILED", message="回测执行超时")
        except Exception as error:
            self.json_store.write(
                self.paths.backtest_dir(run_id) / "error.json",
                {"type": type(error).__name__, "message": str(error)},
            )
            await self._update(
                run_id,
                status="FAILED",
                message=str(error),
                error={"type": type(error).__name__, "message": str(error)},
            )

    def list(self) -> list[dict]:
        return [self._as_summary(task) for task in self.tasks.list(kind="bt")]

    def get(self, run_id: str) -> dict:
        return self._as_summary(self.tasks.get(run_id))

    async def cancel(self, run_id: str) -> dict:
        task = self.tasks.get(run_id)
        if task["status"] not in {"PENDING", "RUNNING"}:
            raise AppError("BACKTEST_NOT_RUNNING", "回测任务已经结束", status_code=409)
        future = self._futures.get(run_id)
        if future:
            future.cancel()
        task = await self._update(run_id, status="CANCELED", message="回测已取消")
        return self._as_summary(task)

    def records(self, run_id: str, kind: str) -> list[dict]:
        self.tasks.get(run_id)
        if kind not in {"trades", "equity"}:
            raise AppError("BACKTEST_RESULT_INVALID", "回测结果类型无效")
        path = self.paths.backtest_dir(run_id) / f"{kind}.parquet"
        if not path.exists():
            return []
        try:
            import pyarrow.parquet as pq
        except ImportError as error:
            raise AppError("STORAGE_DEPENDENCY_MISSING", "未安装 PyArrow") from error
        return pq.read_table(path).to_pylist()
