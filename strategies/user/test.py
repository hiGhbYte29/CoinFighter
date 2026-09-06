from app.modules.strategies.base import Bar, Strategy, StrategyContext


class MyStrategy(Strategy):
    name = "test"
    description = "用户策略"
    default_parameters = {}

    def on_bar(self, context: StrategyContext, bar: Bar) -> None:
        # 示例：在这里读取 context.closes() 并产生模拟交易信号
        pass
