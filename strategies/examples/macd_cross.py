from app.modules.strategies.base import Bar, Strategy, StrategyContext


class MacdCross(Strategy):
    name = "macd_cross"
    description = "由旧版 CoinFighter 迁移的 MACD 交叉策略（现货多头版）"
    default_parameters = {"fast_period": 12, "slow_period": 26, "signal_period": 9}

    def initialize(self, context: StrategyContext) -> None:
        fast = int(context.parameters.get("fast_period", 12))
        slow = int(context.parameters.get("slow_period", 26))
        signal = int(context.parameters.get("signal_period", 9))
        if min(fast, slow, signal) <= 0 or fast >= slow:
            raise ValueError("MACD 周期必须为正数且快速周期小于慢速周期")
        self.fast_ema = None
        self.slow_ema = None
        self.signal_ema = None
        self.previous_above = False

    @staticmethod
    def _ema(previous: float | None, value: float, period: int) -> float:
        return value if previous is None else previous + 2 / (period + 1) * (value - previous)

    def on_bar(self, context: StrategyContext, bar: Bar) -> None:
        fast_period = int(context.parameters.get("fast_period", 12))
        slow_period = int(context.parameters.get("slow_period", 26))
        signal_period = int(context.parameters.get("signal_period", 9))
        self.fast_ema = self._ema(self.fast_ema, bar.close, fast_period)
        self.slow_ema = self._ema(self.slow_ema, bar.close, slow_period)
        macd = self.fast_ema - self.slow_ema
        self.signal_ema = self._ema(self.signal_ema, macd, signal_period)
        if len(context.closes()) < slow_period + signal_period - 1:
            return
        above = macd > self.signal_ema
        if above and not self.previous_above and context.position == 0:
            context.buy()
        elif not above and self.previous_above and context.position > 0:
            context.close_position()
        self.previous_above = above
