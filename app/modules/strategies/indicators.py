def simple_moving_average(values: list[float], period: int) -> float | None:
    if period <= 0:
        raise ValueError("周期必须大于零")
    if len(values) < period:
        return None
    return sum(values[-period:]) / period


def exponential_moving_average(values: list[float], period: int) -> float | None:
    if period <= 0:
        raise ValueError("周期必须大于零")
    if len(values) < period:
        return None
    multiplier = 2 / (period + 1)
    result = sum(values[:period]) / period
    for value in values[period:]:
        result = (value - result) * multiplier + result
    return result
