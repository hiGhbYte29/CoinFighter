from app.modules.strategies.base import Bar, Strategy, StrategyContext
from app.modules.strategies.indicators import simple_moving_average


class MovingAverageCross(Strategy):
    name = "moving_average"
    description = "短期均线上穿长期均线买入，下穿时清仓"
    default_parameters = {"fast_period": 10, "slow_period": 30}

    def initialize(self, context: StrategyContext) -> None:
        self.was_above = False

    def on_bar(self, context: StrategyContext, bar: Bar) -> None:
        fast_period = int(context.parameters.get("fast_period", 10))
        slow_period = int(context.parameters.get("slow_period", 30))
        closes = context.closes(slow_period)
        fast = simple_moving_average(closes, fast_period)
        slow = simple_moving_average(closes, slow_period)
        if fast is None or slow is None:
            return
        above = fast > slow
        if above and not self.was_above and context.position == 0:
            context.buy()
        elif not above and self.was_above and context.position > 0:
            context.close_position()
        self.was_above = above
