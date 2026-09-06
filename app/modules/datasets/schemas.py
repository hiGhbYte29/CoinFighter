from datetime import UTC, datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator


class DatasetDownloadRequest(BaseModel):
    provider: str = "binance"
    market_type: str = "spot"
    symbol: str = "BTC/USDT"
    timeframe: str = Field(default="1h", pattern=r"^\d+[mhdw]$")
    start: datetime
    end: datetime

    @field_validator("start", "end")
    @classmethod
    def require_timezone(cls, value: datetime) -> datetime:
        if value.tzinfo is None:
            value = value.replace(tzinfo=UTC)
        return value.astimezone(UTC)

    @model_validator(mode="after")
    def validate_range(self):
        if self.end <= self.start:
            raise ValueError("结束时间必须晚于开始时间")
        return self


class DatasetMetadata(BaseModel):
    dataset_id: str
    provider: str
    market_type: str
    symbol: str
    timeframe: str
    start: datetime
    end: datetime
    rows: int = 0
    updated_at: datetime
    path: str


class DatasetValidation(BaseModel):
    dataset_id: str
    valid: bool
    rows: int
    duplicate_count: int
    invalid_ohlc_count: int
    gap_count: int
    warnings: list[str]


class DatasetTask(BaseModel):
    task_id: str
    kind: Literal["download"] = "download"
    status: str
    progress: int
    message: str
