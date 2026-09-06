from datetime import UTC, datetime
from pathlib import Path

from app.core.exceptions import AppError
from app.infrastructure.storage.json_store import JsonStore
from app.modules.datasets.schemas import DatasetMetadata


class DatasetCatalog:
    def __init__(self, path: Path, json_store: JsonStore) -> None:
        self.path = path
        self.json_store = json_store

    def list(self) -> list[DatasetMetadata]:
        payload = self.json_store.read(self.path, {"datasets": []})
        return [DatasetMetadata.model_validate(item) for item in payload.get("datasets", [])]

    def get(self, dataset_id: str) -> DatasetMetadata:
        for dataset in self.list():
            if dataset.dataset_id == dataset_id:
                return dataset
        raise AppError("DATASET_NOT_FOUND", "没有找到指定的数据集", status_code=404)

    def find(
        self, provider: str, market_type: str, symbol: str, timeframe: str
    ) -> DatasetMetadata | None:
        identity = (provider.lower(), market_type.lower(), symbol.upper(), timeframe)
        return next(
            (
                item
                for item in self.list()
                if (item.provider, item.market_type, item.symbol, item.timeframe) == identity
            ),
            None,
        )

    def upsert(self, metadata: DatasetMetadata) -> DatasetMetadata:
        datasets = [item for item in self.list() if item.dataset_id != metadata.dataset_id]
        datasets.append(metadata)
        datasets.sort(key=lambda item: item.dataset_id)
        self.json_store.write(
            self.path,
            {"datasets": [item.model_dump(mode="json") for item in datasets]},
        )
        return metadata


def build_metadata(
    *,
    dataset_id: str,
    provider: str,
    market_type: str,
    symbol: str,
    timeframe: str,
    rows: list[dict],
    path: Path,
) -> DatasetMetadata:
    return DatasetMetadata(
        dataset_id=dataset_id,
        provider=provider.lower(),
        market_type=market_type.lower(),
        symbol=symbol.upper(),
        timeframe=timeframe,
        start=datetime.fromtimestamp(rows[0]["timestamp"] / 1000, tz=UTC),
        end=datetime.fromtimestamp(rows[-1]["timestamp"] / 1000, tz=UTC),
        rows=len(rows),
        updated_at=datetime.now(UTC),
        path=str(path),
    )
