from typing import Any, Literal

from pydantic import BaseModel, Field

from app.modules.market.schemas import Candle

IndicatorPlacement = Literal["main", "sub"]
RenderType = Literal["line", "bar", "scatter"]


class IndicatorParameter(BaseModel):
    key: str
    label: str
    type: Literal["integer", "number", "integer_list", "select"]
    default: Any
    minimum: float | None = None
    maximum: float | None = None
    max_items: int | None = None
    options: list[dict[str, str]] = Field(default_factory=list)


class IndicatorDefinition(BaseModel):
    id: str
    name: str
    description: str
    placement: IndicatorPlacement
    parameters: list[IndicatorParameter] = Field(default_factory=list)
    available: bool = True
    unavailable_reason: str | None = None


class IndicatorCatalog(BaseModel):
    formula_version: int = 1
    items: list[IndicatorDefinition]


class IndicatorSelection(BaseModel):
    instance_id: str = Field(pattern=r"^[A-Za-z0-9_-]{1,64}$")
    indicator_id: str = Field(pattern=r"^[a-z0-9_]{2,32}$")
    placement: IndicatorPlacement
    parameters: dict[str, Any] = Field(default_factory=dict)


class ChartDataRequest(BaseModel):
    provider: str = "binance"
    market_type: str = "spot"
    symbol: str = "BTC/USDT"
    timeframe: str = Field(default="1m", pattern=r"^\d+[mhdw]$")
    visible_limit: int = Field(default=300, ge=50, le=500)
    indicators: list[IndicatorSelection] = Field(default_factory=list, max_length=20)


class IndicatorGuide(BaseModel):
    value: float
    label: str | None = None


class IndicatorPlot(BaseModel):
    key: str
    label: str
    render_type: RenderType
    values: list[float | None]
    color: str


class IndicatorOutput(BaseModel):
    instance_id: str
    indicator_id: str
    label: str
    placement: IndicatorPlacement
    plots: list[IndicatorPlot]
    guides: list[IndicatorGuide] = Field(default_factory=list)
    axis_min: float | None = None
    axis_max: float | None = None


class ChartDataResponse(BaseModel):
    formula_version: int = 1
    candles: list[Candle]
    indicators: list[IndicatorOutput]
