from pathlib import Path

from app.infrastructure.storage.json_store import JsonStore
from app.infrastructure.storage.parquet import ParquetStorage


def write_report(
    directory: Path, result: dict, json_store: JsonStore, parquet: ParquetStorage
) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    json_store.write(directory / "metrics.json", result["metrics"])
    parquet.write_records(directory / "trades.parquet", result["trades"])
    parquet.write_records(directory / "equity.parquet", result["equity"])
