from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "CoinFighter"
    app_env: str = "development"
    host: str = "127.0.0.1"
    port: int = 8000
    api_prefix: str = "/api/v1"
    default_provider: str = "binance"
    default_market_type: str = "spot"
    ccxt_enable_rate_limit: bool = True
    http_timeout_seconds: float = 30.0
    max_download_tasks: int = Field(default=2, ge=1, le=8)
    max_backtest_processes: int = Field(default=2, ge=1, le=8)
    backtest_timeout_seconds: int = Field(default=3600, ge=10)
    log_level: str = "INFO"
    local_data_dir: Path = PROJECT_ROOT / "local_data"
    strategy_dir: Path = PROJECT_ROOT / "strategies" / "user"
    example_strategy_dir: Path = PROJECT_ROOT / "strategies" / "examples"
    frontend_dist_dir: Path = PROJECT_ROOT / "frontend" / "dist"
    parquet_compression: str = "zstd"

    def ensure_directories(self) -> None:
        for path in (
            self.local_data_dir / "market",
            self.local_data_dir / "catalog" / "tasks",
            self.local_data_dir / "cache",
            self.local_data_dir / "backtests",
            self.strategy_dir,
            self.example_strategy_dir,
        ):
            path.mkdir(parents=True, exist_ok=True)


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    settings.ensure_directories()
    return settings
