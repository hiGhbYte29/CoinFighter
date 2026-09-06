from app.modules.strategies.base import Bar, Strategy, StrategyContext


class BuyAndHold(Strategy):
    name = "buy_and_hold"
    description = "第一根 K 线满仓买入并持有到回测结束"
    default_parameters = {}

    def initialize(self, context: StrategyContext) -> None:
        self.entered = False

    def on_bar(self, context: StrategyContext, bar: Bar) -> None:
        if not self.entered:
            context.buy()
            self.entered = True
