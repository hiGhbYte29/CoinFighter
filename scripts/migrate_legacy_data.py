"""Convert legacy CoinFighter CSV datasets into the local Parquet catalog."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

from app.core.config import get_settings
from app.infrastructure.storage import JsonStore, ParquetStorage, StoragePaths
from app.modules.datasets.catalog import DatasetCatalog, build_metadata
from app.modules.datasets.service import dataset_id_for


def market_type_for(exchange: str) -> str:
    return "swap" if exchange.endswith(("usdm", "coinm")) else "spot"


def read_legacy_csv(path: Path) -> list[dict]:
    rows: list[dict] = []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        for item in csv.DictReader(handle):
            rows.append(
                {
                    "timestamp": int(item["timestamp"]),
                    "open": float(item["open"]),
                    "high": float(item["high"]),
                    "low": float(item["low"]),
                    "close": float(item["close"]),
                    "volume": float(item["volume"]),
                    "is_closed": True,
                }
            )
    return rows


def migrate(source_directory: Path, target_directory: Path) -> list[dict]:
    paths = StoragePaths(target_directory)
    json_store = JsonStore()
    storage = ParquetStorage(paths)
    catalog = DatasetCatalog(paths.catalog / "datasets.json", json_store)
    migrated: dict[str, dict] = {}
    for csv_path in sorted(source_directory.glob("*.csv")):
        metadata_path = csv_path.with_name(f"{csv_path.name}.meta.json")
        if not metadata_path.exists():
            continue
        legacy = json.loads(metadata_path.read_text(encoding="utf-8"))
        provider = str(legacy["exchange"]).lower()
        symbol = str(legacy["symbol"]).upper()
        timeframe = str(legacy["timeframe"])
        market_type = market_type_for(provider)
        rows = read_legacy_csv(csv_path)
        if not rows:
            continue
        storage.merge_candles(provider, market_type, symbol, timeframe, rows)
        directory = paths.dataset_dir(provider, market_type, symbol, timeframe)
        combined = storage.read_candles(directory)
        identifier = dataset_id_for(provider, market_type, symbol, timeframe)
        item = build_metadata(
            dataset_id=identifier,
            provider=provider,
            market_type=market_type,
            symbol=symbol,
            timeframe=timeframe,
            rows=combined,
            path=directory,
        )
        catalog.upsert(item)
        migrated[identifier] = item.model_dump(mode="json")
    return list(migrated.values())


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path, help="旧版 dataSets 目录")
    parser.add_argument("--target", type=Path, default=get_settings().local_data_dir)
    arguments = parser.parse_args()
    result = migrate(arguments.source.resolve(), arguments.target.resolve())
    print(json.dumps({"migrated": result}, ensure_ascii=False, indent=2, default=str))


if __name__ == "__main__":
    main()
