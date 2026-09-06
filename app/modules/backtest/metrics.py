import math
import statistics

from app.modules.market.timeframes import timeframe_milliseconds


def calculate_metrics(
    equity_rows: list[dict], trades: list[dict], initial_cash: float, timeframe: str
) -> dict:
    if not equity_rows:
        return {}
    equities = [float(row["equity"]) for row in equity_rows]
    total_return = equities[-1] / initial_cash - 1
    peak = equities[0]
    max_drawdown = 0.0
    for value in equities:
        peak = max(peak, value)
        if peak:
            max_drawdown = max(max_drawdown, 1 - value / peak)
    returns = [
        right / left - 1 for left, right in zip(equities, equities[1:], strict=False) if left
    ]
    periods_per_year = 365 * 86_400_000 / timeframe_milliseconds(timeframe)
    sharpe = 0.0
    if len(returns) > 1 and (deviation := statistics.stdev(returns)) > 0:
        sharpe = statistics.mean(returns) / deviation * math.sqrt(periods_per_year)
    duration_ms = equity_rows[-1]["timestamp"] - equity_rows[0]["timestamp"]
    years = duration_ms / (365 * 86_400_000) if duration_ms > 0 else 0
    annualized_return = (equities[-1] / initial_cash) ** (1 / years) - 1 if years > 0 else 0
    exits = [trade for trade in trades if trade["side"] == "SELL"]
    wins = [trade for trade in exits if trade["realized_pnl"] > 0]
    gross_profit = sum(max(0.0, trade["realized_pnl"]) for trade in exits)
    gross_loss = abs(sum(min(0.0, trade["realized_pnl"]) for trade in exits))
    return {
        "initial_cash": initial_cash,
        "final_equity": equities[-1],
        "total_return": total_return,
        "buy_hold_return": equity_rows[-1]["close"] / equity_rows[0]["close"] - 1,
        "annualized_return": annualized_return,
        "max_drawdown": max_drawdown,
        "sharpe_ratio": sharpe,
        "trade_count": len(trades),
        "closed_trade_count": len(exits),
        "win_rate": len(wins) / len(exits) if exits else 0.0,
        "profit_factor": gross_profit / gross_loss if gross_loss else None,
        "total_fees": sum(trade["fee"] for trade in trades),
    }
