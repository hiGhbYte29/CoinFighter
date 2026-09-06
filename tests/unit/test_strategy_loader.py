from pathlib import Path

from app.modules.strategies.loader import StrategyLoader


def test_strategy_loader_creates_and_validates_user_strategy(tmp_path: Path) -> None:
    user = tmp_path / "user"
    examples = tmp_path / "examples"
    loader = StrategyLoader(user, examples)
    created = loader.create("hello_strategy")
    assert created.valid
    assert loader.load_class("hello_strategy").name == "hello_strategy"


def test_strategy_loader_reports_syntax_error(tmp_path: Path) -> None:
    loader = StrategyLoader(tmp_path / "user", tmp_path / "examples")
    result = loader.save("broken_strategy", "class Broken(Strategy):\n  def")
    assert not result.valid
    assert result.errors
