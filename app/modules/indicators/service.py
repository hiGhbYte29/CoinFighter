from collections.abc import Callable
from typing import Any

from app.core.exceptions import AppError
from app.modules.indicators.catalog import CATALOG, DEFINITIONS
from app.modules.indicators.schemas import (
    IndicatorCatalog,
    IndicatorGuide,
    IndicatorOutput,
    IndicatorPlot,
    IndicatorSelection,
)
from app.modules.market.schemas import Candle
from coinfighter.indicators import (
    bollinger_bands,
    cci,
    ema,
    kdj,
    macd,
    mfi,
    obv,
    parabolic_sar,
    rsi,
    sma,
    stoch_rsi,
    supertrend,
    trix,
    vwap,
    williams_r,
    wma,
)

PALETTE = [
    "#ffd43b",
    "#e649a7",
    "#a97ee8",
    "#54c6df",
    "#50b46a",
    "#ff7a2f",
]


def _integer(parameters: dict[str, Any], key: str, default: int) -> int:
    value = parameters.get(key, default)
    if isinstance(value, bool):
        raise ValueError(f"{key} 必须是正整数")
    try:
        numeric = int(value)
    except (TypeError, ValueError) as error:
        raise ValueError(f"{key} 必须是正整数") from error
    if numeric <= 0 or numeric > 500:
        raise ValueError(f"{key} 必须在 1 到 500 之间")
    return numeric


def _number(parameters: dict[str, Any], key: str, default: float) -> float:
    try:
        return float(parameters.get(key, default))
    except (TypeError, ValueError) as error:
        raise ValueError(f"{key} 必须是数字") from error


def _periods(parameters: dict[str, Any], default: list[int]) -> list[int]:
    value = parameters.get("periods", default)
    if not isinstance(value, list) or not 1 <= len(value) <= 6:
        raise ValueError("periods 必须包含 1 到 6 个周期")
    periods = [_integer({"period": item}, "period", 1) for item in value]
    if len(set(periods)) != len(periods):
        raise ValueError("periods 不能包含重复周期")
    return periods


def _period_lines(
    parameters: dict[str, Any], default: list[int]
) -> list[tuple[int, int, str | None]]:
    value = parameters.get("lines")
    if value is None:
        source = str(parameters.get("source", "close"))
        return [
            (index, period, source)
            for index, period in enumerate(_periods(parameters, default), 1)
        ]
    if not isinstance(value, list) or not 1 <= len(value) <= 6:
        raise ValueError("lines 必须包含 1 到 6 条已启用线")

    result: list[tuple[int, int, str | None]] = []
    slots: set[int] = set()
    for item in value:
        if not isinstance(item, dict):
            raise ValueError("lines 中的每一项必须是对象")
        slot = _integer(item, "slot", len(result) + 1)
        if slot > 6 or slot in slots:
            raise ValueError("lines 的 slot 必须是 1 到 6 之间且不能重复")
        slots.add(slot)
        period = _integer(item, "period", 1)
        source = str(item.get("source")) if item.get("source") is not None else None
        result.append((slot, period, source))
    return result


def _plot(
    key: str,
    label: str,
    values: list[float | None],
    index: int = 0,
    render_type: str = "line",
) -> IndicatorPlot:
    return IndicatorPlot(
        key=key,
        label=label,
        render_type=render_type,  # type: ignore[arg-type]
        values=values,
        color=PALETTE[index % len(PALETTE)],
    )


class IndicatorService:
    def catalog(self) -> IndicatorCatalog:
        return CATALOG

    def required_history(self, selections: list[IndicatorSelection]) -> int:
        required = 0
        for selection in selections:
            parameters = selection.parameters
            periods = parameters.get("periods")
            candidates = list(periods) if isinstance(periods, list) else []
            lines = parameters.get("lines")
            if isinstance(lines, list):
                candidates.extend(
                    line.get("period") for line in lines if isinstance(line, dict)
                )
            candidates.extend(
                parameters.get(key)
                for key in ("period", "fast", "slow", "signal", "rsi_period", "stoch_period")
                if parameters.get(key) is not None
            )
            numeric = [int(value) for value in candidates if str(value).isdigit()]
            required = max(required, max(numeric, default=0))
            if selection.indicator_id == "trix":
                required = max(required, _integer(parameters, "period", 12) * 3)
        return min(500, max(50, required * 3))

    def calculate(
        self, candles: list[Candle], selections: list[IndicatorSelection]
    ) -> list[IndicatorOutput]:
        outputs: list[IndicatorOutput] = []
        for selection in selections:
            definition = DEFINITIONS.get(selection.indicator_id)
            if definition is None:
                raise AppError(
                    "INDICATOR_NOT_FOUND",
                    f"未知技术指标：{selection.indicator_id}",
                    status_code=422,
                )
            if not definition.available:
                raise AppError(
                    "INDICATOR_UNAVAILABLE",
                    definition.unavailable_reason or "该指标当前不可用",
                    status_code=422,
                )
            if selection.placement != definition.placement:
                placement_name = "主图" if definition.placement == "main" else "副图"
                raise AppError(
                    "INDICATOR_PLACEMENT_INVALID",
                    f"{definition.name} 只能显示在{placement_name}",
                    status_code=422,
                )
            try:
                outputs.append(self._calculate_one(candles, selection, definition.name))
            except ValueError as error:
                raise AppError(
                    "INDICATOR_CONFIG_INVALID",
                    f"{definition.name} 参数无效",
                    status_code=422,
                    details={"instance_id": selection.instance_id, "reason": str(error)},
                ) from error
        return outputs

    def _calculate_one(
        self, candles: list[Candle], selection: IndicatorSelection, label: str
    ) -> IndicatorOutput:
        opens = [bar.open for bar in candles]
        highs = [bar.high for bar in candles]
        lows = [bar.low for bar in candles]
        closes = [bar.close for bar in candles]
        volumes = [bar.volume for bar in candles]
        sources = {"open": opens, "high": highs, "low": lows, "close": closes}
        parameters = selection.parameters
        source = str(parameters.get("source", "close"))
        if source not in sources:
            raise ValueError("source 必须是 open、high、low 或 close")
        values = sources[source]
        code = selection.indicator_id
        plots: list[IndicatorPlot]
        guides: list[IndicatorGuide] = []
        axis_min: float | None = None
        axis_max: float | None = None

        moving_functions: dict[str, Callable[[list[float], int], list[float | None]]] = {
            "ma": sma,
            "ema": ema,
            "wma": wma,
        }
        if code in moving_functions:
            lines = _period_lines(parameters, [7, 25, 99])
            plots = []
            for index, (slot, period, line_source) in enumerate(lines):
                selected_source = line_source or source
                if selected_source not in sources:
                    raise ValueError("每条线的 source 必须是 open、high、low 或 close")
                plots.append(_plot(
                    f"{code}_{slot}" if "lines" in parameters else f"{code}_{period}",
                    f"{code.upper()}({period})",
                    moving_functions[code](sources[selected_source], period),
                    index,
                ))
        elif code == "boll":
            period = _integer(parameters, "period", 20)
            result = bollinger_bands(values, period, _number(parameters, "deviation", 2))
            plots = [
                _plot("upper", "UPPER", result.upper, 0),
                _plot("middle", "MID", result.middle, 1),
                _plot("lower", "LOWER", result.lower, 2),
            ]
        elif code == "vwap":
            period = _integer(parameters, "period", 20)
            plots = [_plot("vwap", f"VWAP({period})", vwap(highs, lows, closes, volumes, period))]
        elif code == "sar":
            result = parabolic_sar(
                highs,
                lows,
                closes,
                _number(parameters, "step", 0.02),
                _number(parameters, "maximum", 0.2),
            )
            plots = [_plot("sar", "SAR", result, render_type="scatter")]
        elif code == "super":
            period = _integer(parameters, "period", 10)
            result = supertrend(highs, lows, closes, period, _number(parameters, "multiplier", 3))
            rising = [
                value if direction is not None and direction > 0 else None
                for value, direction in zip(result.value, result.direction, strict=True)
            ]
            falling = [
                value if direction is not None and direction < 0 else None
                for value, direction in zip(result.value, result.direction, strict=True)
            ]
            plots = [
                _plot("up", "SUPER UP", rising, 4),
                _plot("down", "SUPER DOWN", falling, 1),
            ]
        elif code == "vol":
            lines = _period_lines(parameters, [7, 14])
            plots = [_plot("volume", "VOL", [*volumes], 0, "bar")]
            plots.extend(
                _plot(
                    f"mavol_{slot}" if "lines" in parameters else f"mavol_{period}",
                    f"MAVOL({period})",
                    sma(volumes, period),
                    index + 3,
                )
                for index, (slot, period, _) in enumerate(lines)
            )
        elif code == "macd":
            fast = _integer(parameters, "fast", 12)
            slow = _integer(parameters, "slow", 26)
            signal = _integer(parameters, "signal", 9)
            result = macd(closes, fast, slow, signal)
            plots = [
                _plot("histogram", "HIST", result.histogram, 0, "bar"),
                _plot("macd", "MACD", result.macd, 3),
                _plot("signal", "SIGNAL", result.signal, 1),
            ]
            guides = [IndicatorGuide(value=0)]
        elif code == "rsi":
            lines = _period_lines(parameters, [6, 12, 24])
            plots = [
                _plot(
                    f"rsi_{slot}" if "lines" in parameters else f"rsi_{period}",
                    f"RSI({period})",
                    rsi(closes, period),
                    index,
                )
                for index, (slot, period, _) in enumerate(lines)
            ]
            guides = [IndicatorGuide(value=30), IndicatorGuide(value=70)]
            axis_min, axis_max = 0, 100
        elif code == "mfi":
            period = _integer(parameters, "period", 14)
            plots = [_plot("mfi", f"MFI({period})", mfi(highs, lows, closes, volumes, period))]
            guides = [IndicatorGuide(value=20), IndicatorGuide(value=80)]
            axis_min, axis_max = 0, 100
        elif code == "kdj":
            period = _integer(parameters, "period", 9)
            result = kdj(
                highs,
                lows,
                closes,
                period,
                _integer(parameters, "smooth_k", 3),
                _integer(parameters, "smooth_d", 3),
            )
            plots = [
                _plot("k", "K", result.k, 0),
                _plot("d", "D", result.d, 1),
                _plot("j", "J", result.j, 2),
            ]
            guides = [IndicatorGuide(value=20), IndicatorGuide(value=80)]
        elif code == "obv":
            plots = [_plot("obv", "OBV", obv(closes, volumes))]
        elif code == "cci":
            period = _integer(parameters, "period", 20)
            plots = [_plot("cci", f"CCI({period})", cci(highs, lows, closes, period))]
            guides = [IndicatorGuide(value=-100), IndicatorGuide(value=100)]
        elif code == "stochrsi":
            result = stoch_rsi(
                closes,
                _integer(parameters, "rsi_period", 14),
                _integer(parameters, "stoch_period", 14),
                _integer(parameters, "smooth_k", 3),
                _integer(parameters, "smooth_d", 3),
            )
            plots = [_plot("k", "K", result.k, 0), _plot("d", "D", result.d, 1)]
            guides = [IndicatorGuide(value=20), IndicatorGuide(value=80)]
            axis_min, axis_max = 0, 100
        elif code == "wr":
            period = _integer(parameters, "period", 14)
            plots = [_plot("wr", f"WR({period})", williams_r(highs, lows, closes, period))]
            guides = [IndicatorGuide(value=-80), IndicatorGuide(value=-20)]
            axis_min, axis_max = -100, 0
        elif code == "trix":
            period = _integer(parameters, "period", 12)
            result = trix(closes, period, _integer(parameters, "signal", 9))
            plots = [
                _plot("trix", "TRIX", result.trix, 0),
                _plot("signal", "SIGNAL", result.signal, 1),
            ]
            guides = [IndicatorGuide(value=0)]
        else:
            raise ValueError("指标尚未实现")

        return IndicatorOutput(
            instance_id=selection.instance_id,
            indicator_id=code,
            label=label,
            placement=selection.placement,
            plots=plots,
            guides=guides,
            axis_min=axis_min,
            axis_max=axis_max,
        )
