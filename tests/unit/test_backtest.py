from app.modules.backtest.engine import run_engine
from app.modules.strategies.base import Bar, Strategy, StrategyContext


class EnterOnce(Strategy):
    def initialize(self, context: StrategyContext) -> None:
        self.entered = False

    def on_bar(self, context: StrategyContext, bar: Bar) -> None:
        if not self.entered:
            context.buy()
            self.entered = True


def test_signal_is_filled_on_next_bar_open() -> None:
    rows = [
        {
            "timestamp": 1_700_000_000_000 + index * 3_600_000,
            "open": 100 + index,
            "high": 102 + index,
            "low": 99 + index,
            "close": 101 + index,
            "volume": 10,
            "is_closed": True,
        }
        for index in range(20)
    ]
    result = run_engine(
        rows,
        EnterOnce,
        {},
        initial_cash=10_000,
        fee_rate=0,
        slippage=0,
        timeframe="1h",
    )
    assert result["trades"][0]["timestamp"] == rows[1]["timestamp"]
    assert result["trades"][0]["price"] == rows[1]["open"]
    assert result["metrics"]["final_equity"] > 10_000
