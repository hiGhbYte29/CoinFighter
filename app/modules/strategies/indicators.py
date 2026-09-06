from coinfighter.indicators import ema, sma


def simple_moving_average(values: list[float], period: int) -> float | None:
    """Compatibility wrapper for existing strategies that expect only the latest value."""
    result = sma(values, period)
    return result[-1] if result else None


def exponential_moving_average(values: list[float], period: int) -> float | None:
    """Compatibility wrapper for existing strategies that expect only the latest value."""
    result = ema(values, period)
    return result[-1] if result else None
