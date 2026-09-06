def timeframe_milliseconds(timeframe: str) -> int:
    unit = timeframe[-1]
    try:
        value = int(timeframe[:-1])
    except (ValueError, IndexError) as error:
        raise ValueError(f"不支持的周期: {timeframe}") from error

    factors = {"m": 60_000, "h": 3_600_000, "d": 86_400_000, "w": 604_800_000}
    if unit not in factors or value <= 0:
        raise ValueError(f"不支持的周期: {timeframe}")
    return value * factors[unit]
