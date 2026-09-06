"""使用公共 indicators 包实现的 MACD 信号线交叉策略。"""

# 导入整个指标库，策略中的所有指标都通过 indicators.xxx 访问。
import indicators
from app.modules.strategies.base import Bar, Strategy, StrategyContext


class MacdCross(Strategy):
    """MACD 上穿信号线时买入，下穿信号线时清仓。"""

    # 三个周期均可在创建回测时覆盖，无需修改策略源码。
    name = "macd_cross"
    description = "由旧版 CoinFighter 迁移的 MACD 交叉策略（现货多头版）"
    default_parameters = {"fast_period": 12, "slow_period": 26, "signal_period": 9}

    def initialize(self, context: StrategyContext) -> None:
        """校验 MACD 参数并初始化三个增量 EMA 计算器。"""

        fast = int(context.parameters.get("fast_period", 12))
        slow = int(context.parameters.get("slow_period", 26))
        signal = int(context.parameters.get("signal_period", 9))
        if min(fast, slow, signal) <= 0 or fast >= slow:
            raise ValueError("MACD 周期必须为正数且快速周期小于慢速周期")

        # 快慢 EMA 的差是 MACD 线，再对 MACD 线计算 EMA 得到信号线。
        self.fast_ema = indicators.EMA(fast)
        self.slow_ema = indicators.EMA(slow)
        self.signal_ema = indicators.EMA(signal)

        # 保存上一根有效 K 线的相对位置，用于只在真正发生交叉时交易。
        self.previous_above = False

    def on_bar(self, context: StrategyContext, bar: Bar) -> None:
        """逐根更新 MACD，并在 MACD 与信号线交叉时产生交易信号。"""

        # EMA.update() 只处理当前收盘价，适合回测和实时行情逐条更新。
        fast = self.fast_ema.update(bar.close)
        slow = self.slow_ema.update(bar.close)

        # 慢速 EMA 尚未完成预热时，还不能得到有效的 MACD。
        if fast is None or slow is None:
            return

        macd = fast - slow
        signal = self.signal_ema.update(macd)

        # 信号线也需要独立的预热周期。
        if signal is None:
            return

        above = macd > signal

        # 只响应上下关系发生变化的那根 K 线，避免连续重复发出相同信号。
        if above and not self.previous_above and context.position == 0:
            context.buy()
        elif not above and self.previous_above and context.position > 0:
            context.close_position()

        # 记录本根 K 线状态，供下一根 K 线判断是否发生交叉。
        self.previous_above = above
