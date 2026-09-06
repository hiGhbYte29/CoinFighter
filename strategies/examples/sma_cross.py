from app.modules.strategies.base import Bar, Strategy, StrategyContext
from app.modules.strategies.indicators import simple_moving_average


class SmaCross(Strategy):
    name = "sma_cross"
    description = "由旧版 CoinFighter 迁移的 SMA 交叉策略（现货多头版）"
    default_parameters = {"fast_period": 7, "slow_period": 21}

    def initialize(self, context: StrategyContext) -> None:
        fast = int(context.parameters.get("fast_period", 7))
        slow = int(context.parameters.get("slow_period", 21))
        if fast <= 0 or slow <= 0 or fast >= slow:
            raise ValueError("快速 SMA 周期必须为正数且小于慢速 SMA 周期")

    def on_bar(self, context: StrategyContext, bar: Bar) -> None:
        fast_period = int(context.parameters.get("fast_period", 7))
        slow_period = int(context.parameters.get("slow_period", 21))
        closes = context.closes(slow_period)
        fast = simple_moving_average(closes, fast_period)
        slow = simple_moving_average(closes, slow_period)
        if fast is None or slow is None:
            return
        if fast > slow and context.position == 0:
            context.buy()
        elif fast < slow and context.position > 0:
            context.close_position()
