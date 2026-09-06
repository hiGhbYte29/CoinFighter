from app.modules.backtest.portfolio import Portfolio
from app.modules.strategies.base import Signal


class SimulatedBroker:
    def __init__(self, fee_rate: float, slippage: float) -> None:
        self.fee_rate = fee_rate
        self.slippage = slippage

    def execute(
        self, signal: Signal, portfolio: Portfolio, timestamp: int, open_price: float
    ) -> dict | None:
        if signal.side == "BUY":
            price = open_price * (1 + self.slippage)
            maximum = portfolio.cash / (price * (1 + self.fee_rate))
            quantity = min(signal.quantity, maximum) if signal.quantity else maximum
            if quantity <= 1e-12:
                return None
            notional = quantity * price
            fee = notional * self.fee_rate
            portfolio.buy(quantity, price, fee)
            realized = 0.0
        else:
            price = open_price * (1 - self.slippage)
            quantity = (
                min(signal.quantity, portfolio.position) if signal.quantity else portfolio.position
            )
            if quantity <= 1e-12:
                return None
            notional = quantity * price
            fee = notional * self.fee_rate
            realized = portfolio.sell(quantity, price, fee)
        return {
            "timestamp": timestamp,
            "side": signal.side,
            "price": price,
            "quantity": quantity,
            "notional": notional,
            "fee": fee,
            "realized_pnl": realized,
        }
