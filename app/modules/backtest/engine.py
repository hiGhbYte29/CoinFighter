from typing import Any

from app.modules.backtest.broker import SimulatedBroker
from app.modules.backtest.metrics import calculate_metrics
from app.modules.backtest.portfolio import Portfolio
from app.modules.strategies.base import Bar, Signal, Strategy, StrategyContext


def run_engine(
    rows: list[dict],
    strategy_class: type[Strategy],
    parameters: dict[str, Any],
    *,
    initial_cash: float,
    fee_rate: float,
    slippage: float,
    timeframe: str,
) -> dict:
    bars = [
        Bar(
            timestamp=int(row["timestamp"]),
            open=float(row["open"]),
            high=float(row["high"]),
            low=float(row["low"]),
            close=float(row["close"]),
            volume=float(row["volume"]),
        )
        for row in rows
        if row.get("is_closed", True)
    ]
    if len(bars) < 2:
        raise ValueError("回测至少需要两根已收盘 K 线")

    strategy = strategy_class()
    context = StrategyContext({**strategy.default_parameters, **parameters})
    portfolio = Portfolio(initial_cash)
    broker = SimulatedBroker(fee_rate, slippage)
    pending: list[Signal] = []
    trades: list[dict] = []
    equity_rows: list[dict] = []
    strategy.initialize(context)

    for index, bar in enumerate(bars):
        for signal in pending:
            trade = broker.execute(signal, portfolio, bar.timestamp, bar.open)
            if trade:
                trades.append(trade)
        pending = []
        context.update(bar, bars[: index + 1], portfolio.cash, portfolio.position)
        strategy.on_bar(context, bar)
        pending = context.drain_signals()
        equity_rows.append(
            {
                "timestamp": bar.timestamp,
                "cash": portfolio.cash,
                "position": portfolio.position,
                "close": bar.close,
                "equity": portfolio.equity(bar.close),
            }
        )

    context.update(bars[-1], bars, portfolio.cash, portfolio.position)
    strategy.finalize(context)
    metrics = calculate_metrics(equity_rows, trades, initial_cash, timeframe)
    return {"metrics": metrics, "trades": trades, "equity": equity_rows}
