from dataclasses import dataclass


@dataclass
class Portfolio:
    initial_cash: float
    cash: float = 0.0
    position: float = 0.0
    average_price: float = 0.0

    def __post_init__(self) -> None:
        self.cash = self.initial_cash

    def buy(self, quantity: float, price: float, fee: float) -> None:
        cost = quantity * price
        if cost + fee > self.cash + 1e-8:
            raise ValueError("可用资金不足")
        old_cost = self.position * self.average_price
        self.cash -= cost + fee
        self.position += quantity
        self.average_price = (old_cost + cost) / self.position if self.position else 0.0

    def sell(self, quantity: float, price: float, fee: float) -> float:
        if quantity > self.position + 1e-12:
            raise ValueError("持仓数量不足")
        realized = (price - self.average_price) * quantity - fee
        self.cash += quantity * price - fee
        self.position -= quantity
        if self.position <= 1e-12:
            self.position = 0.0
            self.average_price = 0.0
        return realized

    def equity(self, price: float) -> float:
        return self.cash + self.position * price
