from pathlib import Path

import indicators
from app.modules.strategies.base import StrategyContext
from app.modules.strategies.loader import StrategyLoader

EXAMPLE_DIRECTORY = Path(__file__).resolve().parents[2] / "strategies" / "examples"


def test_strategy_loader_creates_and_validates_user_strategy(tmp_path: Path) -> None:
    user = tmp_path / "user"
    examples = tmp_path / "examples"
    loader = StrategyLoader(user, examples)
    created = loader.create("hello_strategy")
    assert created.valid
    assert created.source.startswith("import indicators\n")
    assert loader.load_class("hello_strategy").name == "hello_strategy"


def test_strategy_loader_reports_syntax_error(tmp_path: Path) -> None:
    loader = StrategyLoader(tmp_path / "user", tmp_path / "examples")
    result = loader.save("broken_strategy", "class Broken(Strategy):\n  def")
    assert not result.valid
    assert result.errors


def test_sma_example_uses_public_incremental_indicators(tmp_path: Path) -> None:
    loader = StrategyLoader(tmp_path / "user", EXAMPLE_DIRECTORY)
    strategy_class = loader.load_class("sma_cross")
    strategy = strategy_class()
    strategy.initialize(StrategyContext(strategy.default_parameters))

    assert isinstance(strategy.fast_sma, indicators.SMA)
    assert isinstance(strategy.slow_sma, indicators.SMA)


def test_macd_example_uses_public_incremental_indicators(tmp_path: Path) -> None:
    loader = StrategyLoader(tmp_path / "user", EXAMPLE_DIRECTORY)
    strategy_class = loader.load_class("macd_cross")
    strategy = strategy_class()
    strategy.initialize(StrategyContext(strategy.default_parameters))

    assert isinstance(strategy.fast_ema, indicators.EMA)
    assert isinstance(strategy.slow_ema, indicators.EMA)
    assert isinstance(strategy.signal_ema, indicators.EMA)
