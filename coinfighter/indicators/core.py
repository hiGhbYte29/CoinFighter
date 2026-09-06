from __future__ import annotations

import math
from collections import deque
from collections.abc import Sequence

from coinfighter.indicators.types import (
    BollingerBands,
    KdjResult,
    MacdResult,
    Series,
    StochRsiResult,
    SupertrendResult,
    TrixResult,
)


def _period(value: int, name: str = "period") -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ValueError(f"{name} must be a positive integer")
    return value


def _numbers(values: Sequence[float], name: str = "values") -> list[float]:
    result = [float(value) for value in values]
    if any(not math.isfinite(value) for value in result):
        raise ValueError(f"{name} must contain only finite numbers")
    return result


def _same_length(**series: Sequence[float]) -> dict[str, list[float]]:
    converted = {name: _numbers(values, name) for name, values in series.items()}
    lengths = {len(values) for values in converted.values()}
    if len(lengths) > 1:
        raise ValueError("indicator inputs must have the same length")
    return converted


def _ema_optional(values: Series, period: int) -> Series:
    period = _period(period)
    result: Series = [None] * len(values)
    populated = [(index, value) for index, value in enumerate(values) if value is not None]
    if len(populated) < period:
        return result
    seed = sum(float(value) for _, value in populated[:period]) / period
    seed_index = populated[period - 1][0]
    result[seed_index] = seed
    multiplier = 2 / (period + 1)
    current = seed
    for index, value in populated[period:]:
        current += multiplier * (float(value) - current)
        result[index] = current
    return result


def _rolling_optional(values: Series, period: int) -> Series:
    period = _period(period)
    result: Series = [None] * len(values)
    window: deque[float] = deque()
    total = 0.0
    for index, value in enumerate(values):
        if value is None:
            window.clear()
            total = 0.0
            continue
        numeric = float(value)
        window.append(numeric)
        total += numeric
        if len(window) > period:
            total -= window.popleft()
        if len(window) == period:
            result[index] = total / period
    return result


def sma(values: Sequence[float], period: int) -> Series:
    data = _numbers(values)
    period = _period(period)
    result: Series = [None] * len(data)
    total = 0.0
    for index, value in enumerate(data):
        total += value
        if index >= period:
            total -= data[index - period]
        if index >= period - 1:
            result[index] = total / period
    return result


def ema(values: Sequence[float], period: int) -> Series:
    data = _numbers(values)
    return _ema_optional([*data], period)


def wma(values: Sequence[float], period: int) -> Series:
    data = _numbers(values)
    period = _period(period)
    result: Series = [None] * len(data)
    denominator = period * (period + 1) / 2
    for index in range(period - 1, len(data)):
        window = data[index - period + 1 : index + 1]
        result[index] = sum(value * weight for weight, value in enumerate(window, 1)) / denominator
    return result


def bollinger_bands(
    values: Sequence[float], period: int = 20, deviation: float = 2.0
) -> BollingerBands:
    data = _numbers(values)
    period = _period(period)
    if not math.isfinite(deviation) or deviation <= 0:
        raise ValueError("deviation must be greater than zero")
    middle = sma(data, period)
    upper: Series = [None] * len(data)
    lower: Series = [None] * len(data)
    for index in range(period - 1, len(data)):
        window = data[index - period + 1 : index + 1]
        mean = float(middle[index])
        standard_deviation = math.sqrt(sum((value - mean) ** 2 for value in window) / period)
        upper[index] = mean + deviation * standard_deviation
        lower[index] = mean - deviation * standard_deviation
    return BollingerBands(upper=upper, middle=middle, lower=lower)


def vwap(
    high: Sequence[float],
    low: Sequence[float],
    close: Sequence[float],
    volume: Sequence[float],
    period: int = 20,
) -> Series:
    data = _same_length(high=high, low=low, close=close, volume=volume)
    period = _period(period)
    typical = [
        (high_value + low_value + close_value) / 3
        for high_value, low_value, close_value in zip(
            data["high"], data["low"], data["close"], strict=True
        )
    ]
    result: Series = [None] * len(typical)
    numerator = 0.0
    denominator = 0.0
    for index, (price, amount) in enumerate(zip(typical, data["volume"], strict=True)):
        numerator += price * amount
        denominator += amount
        if index >= period:
            numerator -= typical[index - period] * data["volume"][index - period]
            denominator -= data["volume"][index - period]
        if index >= period - 1 and denominator > 0:
            result[index] = numerator / denominator
    return result


def true_range(high: Sequence[float], low: Sequence[float], close: Sequence[float]) -> list[float]:
    data = _same_length(high=high, low=low, close=close)
    result: list[float] = []
    for index, (high_value, low_value) in enumerate(zip(data["high"], data["low"], strict=True)):
        if index == 0:
            result.append(high_value - low_value)
        else:
            previous = data["close"][index - 1]
            result.append(
                max(
                    high_value - low_value,
                    abs(high_value - previous),
                    abs(low_value - previous),
                )
            )
    return result


def atr(
    high: Sequence[float], low: Sequence[float], close: Sequence[float], period: int = 14
) -> Series:
    ranges = true_range(high, low, close)
    period = _period(period)
    result: Series = [None] * len(ranges)
    if len(ranges) < period:
        return result
    current = sum(ranges[:period]) / period
    result[period - 1] = current
    for index in range(period, len(ranges)):
        current = (current * (period - 1) + ranges[index]) / period
        result[index] = current
    return result


def macd(values: Sequence[float], fast: int = 12, slow: int = 26, signal: int = 9) -> MacdResult:
    data = _numbers(values)
    fast = _period(fast, "fast")
    slow = _period(slow, "slow")
    signal = _period(signal, "signal")
    if fast >= slow:
        raise ValueError("fast must be smaller than slow")
    fast_line = ema(data, fast)
    slow_line = ema(data, slow)
    line: Series = [
        None if first is None or second is None else first - second
        for first, second in zip(fast_line, slow_line, strict=True)
    ]
    signal_line = _ema_optional(line, signal)
    histogram: Series = [
        None if first is None or second is None else first - second
        for first, second in zip(line, signal_line, strict=True)
    ]
    return MacdResult(macd=line, signal=signal_line, histogram=histogram)


def rsi(values: Sequence[float], period: int = 14) -> Series:
    data = _numbers(values)
    period = _period(period)
    result: Series = [None] * len(data)
    if len(data) <= period:
        return result
    gains = [max(data[index] - data[index - 1], 0.0) for index in range(1, len(data))]
    losses = [max(data[index - 1] - data[index], 0.0) for index in range(1, len(data))]
    average_gain = sum(gains[:period]) / period
    average_loss = sum(losses[:period]) / period

    def value() -> float:
        if average_gain == 0 and average_loss == 0:
            return 50.0
        if average_loss == 0:
            return 100.0
        return 100 - 100 / (1 + average_gain / average_loss)

    result[period] = value()
    for index in range(period + 1, len(data)):
        average_gain = (average_gain * (period - 1) + gains[index - 1]) / period
        average_loss = (average_loss * (period - 1) + losses[index - 1]) / period
        result[index] = value()
    return result


def mfi(
    high: Sequence[float],
    low: Sequence[float],
    close: Sequence[float],
    volume: Sequence[float],
    period: int = 14,
) -> Series:
    data = _same_length(high=high, low=low, close=close, volume=volume)
    period = _period(period)
    typical = [
        (high_value + low_value + close_value) / 3
        for high_value, low_value, close_value in zip(
            data["high"], data["low"], data["close"], strict=True
        )
    ]
    positive = [0.0] * len(typical)
    negative = [0.0] * len(typical)
    for index in range(1, len(typical)):
        flow = typical[index] * data["volume"][index]
        if typical[index] > typical[index - 1]:
            positive[index] = flow
        elif typical[index] < typical[index - 1]:
            negative[index] = flow
    result: Series = [None] * len(typical)
    for index in range(period, len(typical)):
        start = index - period + 1
        up = sum(positive[start : index + 1])
        down = sum(negative[start : index + 1])
        result[index] = (
            50.0 if up == down == 0 else 100.0 if down == 0 else 100 - 100 / (1 + up / down)
        )
    return result


def kdj(
    high: Sequence[float],
    low: Sequence[float],
    close: Sequence[float],
    period: int = 9,
    smooth_k: int = 3,
    smooth_d: int = 3,
) -> KdjResult:
    data = _same_length(high=high, low=low, close=close)
    period = _period(period)
    smooth_k = _period(smooth_k, "smooth_k")
    smooth_d = _period(smooth_d, "smooth_d")
    k_line: Series = [None] * len(data["close"])
    d_line: Series = [None] * len(data["close"])
    j_line: Series = [None] * len(data["close"])
    current_k = 50.0
    current_d = 50.0
    for index in range(period - 1, len(data["close"])):
        start = index - period + 1
        highest = max(data["high"][start : index + 1])
        lowest = min(data["low"][start : index + 1])
        rsv = (
            50.0
            if highest == lowest
            else (data["close"][index] - lowest) / (highest - lowest) * 100
        )
        current_k = (current_k * (smooth_k - 1) + rsv) / smooth_k
        current_d = (current_d * (smooth_d - 1) + current_k) / smooth_d
        k_line[index] = current_k
        d_line[index] = current_d
        j_line[index] = 3 * current_k - 2 * current_d
    return KdjResult(k=k_line, d=d_line, j=j_line)


def obv(close: Sequence[float], volume: Sequence[float]) -> Series:
    data = _same_length(close=close, volume=volume)
    if not data["close"]:
        return []
    result: Series = [0.0]
    current = 0.0
    for index in range(1, len(data["close"])):
        if data["close"][index] > data["close"][index - 1]:
            current += data["volume"][index]
        elif data["close"][index] < data["close"][index - 1]:
            current -= data["volume"][index]
        result.append(current)
    return result


def cci(
    high: Sequence[float], low: Sequence[float], close: Sequence[float], period: int = 20
) -> Series:
    data = _same_length(high=high, low=low, close=close)
    period = _period(period)
    typical = [
        (high_value + low_value + close_value) / 3
        for high_value, low_value, close_value in zip(
            data["high"], data["low"], data["close"], strict=True
        )
    ]
    means = sma(typical, period)
    result: Series = [None] * len(typical)
    for index in range(period - 1, len(typical)):
        mean = float(means[index])
        window = typical[index - period + 1 : index + 1]
        mean_deviation = sum(abs(value - mean) for value in window) / period
        result[index] = (
            0.0 if mean_deviation == 0 else (typical[index] - mean) / (0.015 * mean_deviation)
        )
    return result


def stoch_rsi(
    values: Sequence[float],
    rsi_period: int = 14,
    stoch_period: int = 14,
    smooth_k: int = 3,
    smooth_d: int = 3,
) -> StochRsiResult:
    rsi_line = rsi(values, _period(rsi_period, "rsi_period"))
    stoch_period = _period(stoch_period, "stoch_period")
    raw: Series = [None] * len(rsi_line)
    for index in range(len(rsi_line)):
        start = index - stoch_period + 1
        if start < 0 or any(value is None for value in rsi_line[start : index + 1]):
            continue
        window = [float(value) for value in rsi_line[start : index + 1] if value is not None]
        lowest, highest = min(window), max(window)
        raw[index] = (
            50.0
            if highest == lowest
            else (float(rsi_line[index]) - lowest) / (highest - lowest) * 100
        )
    k_line = _rolling_optional(raw, _period(smooth_k, "smooth_k"))
    d_line = _rolling_optional(k_line, _period(smooth_d, "smooth_d"))
    return StochRsiResult(k=k_line, d=d_line)


def williams_r(
    high: Sequence[float], low: Sequence[float], close: Sequence[float], period: int = 14
) -> Series:
    data = _same_length(high=high, low=low, close=close)
    period = _period(period)
    result: Series = [None] * len(data["close"])
    for index in range(period - 1, len(data["close"])):
        start = index - period + 1
        highest = max(data["high"][start : index + 1])
        lowest = min(data["low"][start : index + 1])
        result[index] = (
            0.0
            if highest == lowest
            else -100 * (highest - data["close"][index]) / (highest - lowest)
        )
    return result


def trix(values: Sequence[float], period: int = 12, signal: int = 9) -> TrixResult:
    data = _numbers(values)
    period = _period(period)
    first = ema(data, period)
    second = _ema_optional(first, period)
    third = _ema_optional(second, period)
    line: Series = [None] * len(data)
    previous: float | None = None
    for index, value in enumerate(third):
        if value is None:
            continue
        if previous not in (None, 0):
            line[index] = (value - previous) / previous * 100
        previous = value
    return TrixResult(trix=line, signal=_ema_optional(line, _period(signal, "signal")))


def parabolic_sar(
    high: Sequence[float],
    low: Sequence[float],
    close: Sequence[float],
    step: float = 0.02,
    maximum: float = 0.2,
) -> Series:
    data = _same_length(high=high, low=low, close=close)
    if not (0 < step <= maximum <= 1):
        raise ValueError("SAR requires 0 < step <= maximum <= 1")
    size = len(data["close"])
    if size == 0:
        return []
    result: Series = [None] * size
    if size == 1:
        result[0] = data["low"][0]
        return result
    rising = data["close"][1] >= data["close"][0]
    sar = data["low"][0] if rising else data["high"][0]
    extreme = max(data["high"][:2]) if rising else min(data["low"][:2])
    acceleration = step
    result[0] = sar
    for index in range(1, size):
        sar += acceleration * (extreme - sar)
        if rising:
            sar = min(sar, data["low"][index - 1], data["low"][max(0, index - 2)])
            if data["low"][index] < sar:
                rising = False
                sar = extreme
                extreme = data["low"][index]
                acceleration = step
            elif data["high"][index] > extreme:
                extreme = data["high"][index]
                acceleration = min(maximum, acceleration + step)
        else:
            sar = max(sar, data["high"][index - 1], data["high"][max(0, index - 2)])
            if data["high"][index] > sar:
                rising = True
                sar = extreme
                extreme = data["high"][index]
                acceleration = step
            elif data["low"][index] < extreme:
                extreme = data["low"][index]
                acceleration = min(maximum, acceleration + step)
        result[index] = sar
    return result


def supertrend(
    high: Sequence[float],
    low: Sequence[float],
    close: Sequence[float],
    period: int = 10,
    multiplier: float = 3.0,
) -> SupertrendResult:
    data = _same_length(high=high, low=low, close=close)
    period = _period(period)
    if not math.isfinite(multiplier) or multiplier <= 0:
        raise ValueError("multiplier must be greater than zero")
    atr_line = atr(data["high"], data["low"], data["close"], period)
    size = len(data["close"])
    upper: Series = [None] * size
    lower: Series = [None] * size
    value: Series = [None] * size
    direction: Series = [None] * size
    for index in range(size):
        current_atr = atr_line[index]
        if current_atr is None:
            continue
        midpoint = (data["high"][index] + data["low"][index]) / 2
        basic_upper = midpoint + multiplier * current_atr
        basic_lower = midpoint - multiplier * current_atr
        if index == 0 or upper[index - 1] is None:
            upper[index], lower[index] = basic_upper, basic_lower
        else:
            upper[index] = (
                basic_upper
                if basic_upper < float(upper[index - 1])
                or data["close"][index - 1] > float(upper[index - 1])
                else upper[index - 1]
            )
            lower[index] = (
                basic_lower
                if basic_lower > float(lower[index - 1])
                or data["close"][index - 1] < float(lower[index - 1])
                else lower[index - 1]
            )
        previous_direction = direction[index - 1] if index else None
        if previous_direction is None:
            current_direction = 1.0
        elif previous_direction < 0 and data["close"][index] > float(upper[index]):
            current_direction = 1.0
        elif previous_direction > 0 and data["close"][index] < float(lower[index]):
            current_direction = -1.0
        else:
            current_direction = previous_direction
        direction[index] = current_direction
        value[index] = lower[index] if current_direction > 0 else upper[index]
    return SupertrendResult(value=value, direction=direction)


class SMA:
    """O(1) rolling SMA for on-bar strategies."""

    def __init__(self, period: int) -> None:
        self.period = _period(period)
        self._window: deque[float] = deque()
        self._total = 0.0

    def update(self, value: float) -> float | None:
        numeric = _numbers([value])[0]
        self._window.append(numeric)
        self._total += numeric
        if len(self._window) > self.period:
            self._total -= self._window.popleft()
        return self._total / self.period if len(self._window) == self.period else None


class EMA:
    """Incremental EMA using an SMA seed, matching :func:`ema`."""

    def __init__(self, period: int) -> None:
        self.period = _period(period)
        self._seed: list[float] = []
        self._value: float | None = None

    def update(self, value: float) -> float | None:
        numeric = _numbers([value])[0]
        if self._value is None:
            self._seed.append(numeric)
            if len(self._seed) < self.period:
                return None
            self._value = sum(self._seed) / self.period
            self._seed.clear()
            return self._value
        self._value += 2 / (self.period + 1) * (numeric - self._value)
        return self._value
