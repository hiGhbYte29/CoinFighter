"""使用公共 indicators 包实现的双均线现货多头策略。"""

# 导入整个指标库，新增指标后也可以继续使用 indicators.xxx 的统一写法。
import indicators
from app.modules.strategies.base import Bar, Strategy, StrategyContext


class SmaCross(Strategy):
    """快速 SMA 位于慢速 SMA 上方时持有，位于下方时空仓。"""

    # name 用于 API 和回测任务识别策略，default_parameters 可被用户参数覆盖。
    name = "sma_cross"
    description = "由旧版 CoinFighter 迁移的 SMA 交叉策略（现货多头版）"
    default_parameters = {"fast_period": 7, "slow_period": 21}

    def initialize(self, context: StrategyContext) -> None:
        """读取参数、校验周期，并为本次回测创建增量指标实例。"""

        # context.parameters 已合并默认参数和本次回测传入的参数。
        fast = int(context.parameters.get("fast_period", 7))
        slow = int(context.parameters.get("slow_period", 21))
        if fast <= 0 or slow <= 0 or fast >= slow:
            raise ValueError("快速 SMA 周期必须为正数且小于慢速 SMA 周期")

        # 增量计算器只保存所需窗口，无需在每根 K 线上重新遍历全部历史数据。
        self.fast_sma = indicators.SMA(fast)
        self.slow_sma = indicators.SMA(slow)

    def on_bar(self, context: StrategyContext, bar: Bar) -> None:
        """用当前收盘价更新均线，并根据均线关系产生交易信号。"""

        fast = self.fast_sma.update(bar.close)
        slow = self.slow_sma.update(bar.close)

        # 周期内数据不足时 update() 返回 None，此时指标仍在预热，不应交易。
        if fast is None or slow is None:
            return

        # 这是现货多头策略：金叉区域只持有多仓，死叉区域清空已有多仓。
        if fast > slow and context.position == 0:
            context.buy()
        elif fast < slow and context.position > 0:
            context.close_position()
