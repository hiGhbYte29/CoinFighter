from typing import Any

from pydantic import BaseModel, Field


class BacktestRequest(BaseModel):
    strategy: str
    dataset_id: str
    initial_cash: float = Field(default=100_000, gt=0)
    fee_rate: float = Field(default=0.001, ge=0, le=0.1)
    slippage: float = Field(default=0.0002, ge=0, le=0.1)
    parameters: dict[str, Any] = {}


class BacktestSummary(BaseModel):
    run_id: str
    status: str
    progress: int
    message: str
    request: dict[str, Any]
    result: dict[str, Any] | None = None
    created_at: str
    updated_at: str
