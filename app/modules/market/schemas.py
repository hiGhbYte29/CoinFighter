from pydantic import BaseModel, ConfigDict, Field


class Candle(BaseModel):
    model_config = ConfigDict(extra="ignore")

    timestamp: int
    open: float
    high: float
    low: float
    close: float
    volume: float
    is_closed: bool = True


class Ticker(BaseModel):
    provider: str
    market_type: str
    symbol: str
    timestamp: int | None = None
    last: float | None = None
    open: float | None = None
    high: float | None = None
    low: float | None = None
    change_percent: float | None = None
    base_volume: float | None = None


class CandleQuery(BaseModel):
    provider: str = "binance"
    market_type: str = "spot"
    symbol: str = "BTC/USDT"
    timeframe: str = Field(default="1h", pattern=r"^\d+[mhdw]$")
    limit: int = Field(default=200, ge=1, le=1000)
