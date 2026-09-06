from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

from app.core.exceptions import AppError
from app.infrastructure.storage.paths import StoragePaths


def _pyarrow():
    try:
        import pyarrow as pa
        import pyarrow.parquet as pq
    except ImportError as error:
        raise AppError(
            "STORAGE_DEPENDENCY_MISSING",
            "未安装 PyArrow，无法读写 Parquet",
            status_code=503,
        ) from error
    return pa, pq


def timestamp_ms(value: Any) -> int:
    if isinstance(value, datetime):
        return int(value.timestamp() * 1000)
    return int(value)


class ParquetStorage:
    def __init__(self, paths: StoragePaths, compression: str = "zstd") -> None:
        self.paths = paths
        self.compression = compression

    def _candle_schema(self):
        pa, _ = _pyarrow()
        return pa.schema(
            [
                ("timestamp", pa.timestamp("ms", tz="UTC")),
                ("open", pa.float64()),
                ("high", pa.float64()),
                ("low", pa.float64()),
                ("close", pa.float64()),
                ("volume", pa.float64()),
                ("is_closed", pa.bool_()),
            ]
        )

    @staticmethod
    def _normalize_candle(row: dict) -> dict:
        milliseconds = timestamp_ms(row["timestamp"])
        return {
            "timestamp": datetime.fromtimestamp(milliseconds / 1000, tz=UTC),
            "open": float(row["open"]),
            "high": float(row["high"]),
            "low": float(row["low"]),
            "close": float(row["close"]),
            "volume": float(row["volume"]),
            "is_closed": bool(row.get("is_closed", True)),
        }

    def merge_candles(
        self,
        provider: str,
        market_type: str,
        symbol: str,
        timeframe: str,
        rows: list[dict],
    ) -> list[Path]:
        if not rows:
            return []
        pa, pq = _pyarrow()
        directory = self.paths.dataset_dir(provider, market_type, symbol, timeframe)
        directory.mkdir(parents=True, exist_ok=True)
        monthly: defaultdict[str, list[dict]] = defaultdict(list)
        for row in rows:
            normalized = self._normalize_candle(row)
            monthly[normalized["timestamp"].strftime("%Y-%m")].append(normalized)

        written: list[Path] = []
        for month, new_rows in monthly.items():
            target = directory / f"{month}.parquet"
            all_rows = new_rows
            if target.exists():
                all_rows = pq.read_table(target).to_pylist() + new_rows
            deduplicated = {
                timestamp_ms(row["timestamp"]): self._normalize_candle(row) for row in all_rows
            }
            ordered = [deduplicated[key] for key in sorted(deduplicated)]
            table = pa.Table.from_pylist(ordered, schema=self._candle_schema())
            temporary = target.with_name(f".{target.name}.{uuid4().hex}.tmp")
            pq.write_table(table, temporary, compression=self.compression)
            pq.read_metadata(temporary)
            temporary.replace(target)
            written.append(target)
        return written

    def read_candles(
        self,
        directory: Path,
        *,
        start_ms: int | None = None,
        end_ms: int | None = None,
        limit: int | None = None,
    ) -> list[dict]:
        _, pq = _pyarrow()
        rows: list[dict] = []
        for path in sorted(directory.glob("*.parquet")):
            rows.extend(pq.read_table(path).to_pylist())
        normalized = []
        for row in rows:
            milliseconds = timestamp_ms(row["timestamp"])
            if start_ms is not None and milliseconds < start_ms:
                continue
            if end_ms is not None and milliseconds >= end_ms:
                continue
            item = dict(row)
            item["timestamp"] = milliseconds
            normalized.append(item)
        normalized.sort(key=lambda row: row["timestamp"])
        return normalized[-limit:] if limit else normalized

    def write_records(self, path: Path, records: list[dict]) -> None:
        pa, pq = _pyarrow()
        path.parent.mkdir(parents=True, exist_ok=True)
        table = pa.Table.from_pylist(records)
        temporary = path.with_name(f".{path.name}.{uuid4().hex}.tmp")
        pq.write_table(table, temporary, compression=self.compression)
        pq.read_metadata(temporary)
        temporary.replace(path)
