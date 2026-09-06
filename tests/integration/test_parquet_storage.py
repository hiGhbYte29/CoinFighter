from pathlib import Path

from app.infrastructure.storage.parquet import ParquetStorage
from app.infrastructure.storage.paths import StoragePaths


def test_parquet_storage_partitions_and_deduplicates(tmp_path: Path) -> None:
    storage = ParquetStorage(StoragePaths(tmp_path))
    rows = [
        {
            "timestamp": 1_704_067_200_000,
            "open": 100,
            "high": 105,
            "low": 98,
            "close": 103,
            "volume": 12,
            "is_closed": True,
        },
        {
            "timestamp": 1_704_153_600_000,
            "open": 103,
            "high": 108,
            "low": 102,
            "close": 106,
            "volume": 14,
            "is_closed": True,
        },
    ]
    storage.merge_candles("binance", "spot", "BTC/USDT", "1d", rows)
    storage.merge_candles("binance", "spot", "BTC/USDT", "1d", rows)
    directory = storage.paths.dataset_dir("binance", "spot", "BTC/USDT", "1d")
    restored = storage.read_candles(directory)
    assert len(restored) == 2
    assert restored[0]["close"] == 103
