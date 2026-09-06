from typing import Any

from pydantic import BaseModel, Field


class StrategyInfo(BaseModel):
    name: str
    class_name: str | None = None
    description: str = ""
    default_parameters: dict[str, Any] = {}
    source_path: str
    editable: bool
    valid: bool
    errors: list[str] = []


class StrategyCreate(BaseModel):
    name: str = Field(pattern=r"^[A-Za-z][A-Za-z0-9_]{1,63}$")
    source: str | None = None


class StrategySourceUpdate(BaseModel):
    source: str = Field(min_length=1, max_length=200_000)


class StrategySource(BaseModel):
    name: str
    source: str
    valid: bool
    errors: list[str] = []
