from dataclasses import dataclass
from typing import Any, Literal


@dataclass(frozen=True)
class Bar:
    timestamp: int
    open: float
    high: float
    low: float
    close: float
    volume: float


@dataclass(frozen=True)
class Signal:
    side: Literal["BUY", "SELL"]
    quantity: float | None = None


class StrategyContext:
    def __init__(self, parameters: dict[str, Any]) -> None:
        self.parameters = parameters
        self.bar: Bar | None = None
        self.cash = 0.0
        self.position = 0.0
        self.equity = 0.0
        self._history: list[Bar] = []
        self._signals: list[Signal] = []

    def update(self, bar: Bar, history: list[Bar], cash: float, position: float) -> None:
        self.bar = bar
        self._history = history
        self.cash = cash
        self.position = position
        self.equity = cash + position * bar.close

    def closes(self, window: int | None = None) -> list[float]:
        values = [bar.close for bar in self._history]
        return values[-window:] if window else values

    def buy(self, quantity: float | None = None) -> None:
        if quantity is not None and quantity <= 0:
            raise ValueError("买入数量必须大于零")
        self._signals.append(Signal("BUY", quantity))

    def sell(self, quantity: float | None = None) -> None:
        if quantity is not None and quantity <= 0:
            raise ValueError("卖出数量必须大于零")
        self._signals.append(Signal("SELL", quantity))

    def close_position(self) -> None:
        if self.position > 0:
            self.sell()

    def drain_signals(self) -> list[Signal]:
        signals, self._signals = self._signals, []
        return signals


class Strategy:
    name = "base"
    description = ""
    default_parameters: dict[str, Any] = {}

    def initialize(self, context: StrategyContext) -> None:
        return None

    def on_bar(self, context: StrategyContext, bar: Bar) -> None:
        raise NotImplementedError

    def finalize(self, context: StrategyContext) -> None:
        return None
