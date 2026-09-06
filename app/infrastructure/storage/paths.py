import re
from pathlib import Path

from app.core.exceptions import AppError


def safe_segment(value: str) -> str:
    normalized = re.sub(r"[^A-Za-z0-9_.-]", "", value.replace("/", ""))
    if not normalized or normalized in {".", ".."}:
        raise AppError("SYSTEM_INVALID_PATH", "文件路径包含无效名称")
    return normalized


class StoragePaths:
    def __init__(self, root: Path) -> None:
        self.root = root.resolve()

    @property
    def market(self) -> Path:
        return self.root / "market"

    @property
    def catalog(self) -> Path:
        return self.root / "catalog"

    @property
    def tasks(self) -> Path:
        return self.catalog / "tasks"

    @property
    def backtests(self) -> Path:
        return self.root / "backtests"

    def dataset_dir(self, provider: str, market_type: str, symbol: str, timeframe: str) -> Path:
        return (
            self.market
            / safe_segment(provider.lower())
            / safe_segment(market_type.lower())
            / safe_segment(symbol.upper())
            / safe_segment(timeframe)
        )

    def backtest_dir(self, run_id: str) -> Path:
        return self.backtests / safe_segment(run_id)
