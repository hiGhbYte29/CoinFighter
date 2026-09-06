"""最简单的买入并持有策略，用于演示策略生命周期和下单接口。"""

from app.modules.strategies.base import Bar, Strategy, StrategyContext


class BuyAndHold(Strategy):
    """在第一根 K 线发出买入信号，之后不再交易。"""

    # 这些类属性会显示在策略列表中，并作为创建回测任务时的默认配置。
    name = "buy_and_hold"
    description = "第一根 K 线满仓买入并持有到回测结束"
    default_parameters = {}

    def initialize(self, context: StrategyContext) -> None:
        """每次回测开始前调用，用状态变量防止重复买入。"""

        self.entered = False

    def on_bar(self, context: StrategyContext, bar: Bar) -> None:
        """每收到一根已收盘 K 线调用一次。"""

        if not self.entered:
            # 不指定数量表示使用可用资金买入；信号会在下一根 K 线开盘时成交。
            context.buy()
            self.entered = True
