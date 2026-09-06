from app.modules.datasets.schemas import DatasetValidation
from app.modules.market.timeframes import timeframe_milliseconds


def validate_candles(dataset_id: str, rows: list[dict], timeframe: str) -> DatasetValidation:
    timestamps = [int(row["timestamp"]) for row in rows]
    duplicate_count = len(timestamps) - len(set(timestamps))
    invalid_ohlc_count = sum(
        1
        for row in rows
        if float(row["high"]) < max(float(row["open"]), float(row["close"]))
        or float(row["low"]) > min(float(row["open"]), float(row["close"]))
        or float(row["volume"]) < 0
    )
    step = timeframe_milliseconds(timeframe)
    ordered = sorted(set(timestamps))
    gap_count = sum(
        1 for left, right in zip(ordered, ordered[1:], strict=False) if right - left > step
    )
    warnings = []
    if gap_count:
        warnings.append("数据存在时间缺口；无成交时交易所可能不会生成 K 线")
    if rows and not rows[-1].get("is_closed", True):
        warnings.append("最后一根 K 线尚未收盘，回测时会自动排除")
    return DatasetValidation(
        dataset_id=dataset_id,
        valid=bool(rows) and duplicate_count == 0 and invalid_ohlc_count == 0,
        rows=len(rows),
        duplicate_count=duplicate_count,
        invalid_ohlc_count=invalid_ohlc_count,
        gap_count=gap_count,
        warnings=warnings,
    )
