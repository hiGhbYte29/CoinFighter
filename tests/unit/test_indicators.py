import math

import pytest

from app.modules.indicators.catalog import CATALOG
from app.modules.indicators.schemas import IndicatorSelection
from app.modules.indicators.service import IndicatorService
from app.modules.market.schemas import Candle
from coinfighter.indicators import (
    EMA,
    SMA,
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


def test_batch_and_incremental_averages_match() -> None:
    values = [float(index) for index in range(1, 51)]
    sma_calculator = SMA(7)
    ema_calculator = EMA(7)
    assert [sma_calculator.update(value) for value in values] == sma(values, 7)
    assert [ema_calculator.update(value) for value in values] == ema(values, 7)


def test_constant_series_has_stable_indicators() -> None:
    values = [100.0] * 100
    assert rsi(values, 14)[-1] == 50
    result = macd(values)
    assert result.macd[-1] == pytest.approx(0)
    assert result.signal[-1] == pytest.approx(0)
    bands = bollinger_bands(values)
    assert bands.upper[-1] == bands.middle[-1] == bands.lower[-1] == 100


def test_all_public_batch_indicators_are_aligned_and_finite() -> None:
    close = [100 + index * 0.2 + math.sin(index / 5) for index in range(200)]
    high = [value + 1 for value in close]
    low = [value - 1 for value in close]
    volume = [10 + index % 13 for index in range(200)]
    lines = [
        sma(close, 20),
        ema(close, 20),
        wma(close, 20),
        vwap(high, low, close, volume),
        rsi(close),
        mfi(high, low, close, volume),
        obv(close, volume),
        cci(high, low, close),
        williams_r(high, low, close),
        parabolic_sar(high, low, close),
        *vars(kdj(high, low, close)).values(),
        *vars(stoch_rsi(close)).values(),
        *vars(supertrend(high, low, close)).values(),
        *vars(trix(close)).values(),
        *vars(macd(close)).values(),
        *vars(bollinger_bands(close)).values(),
    ]
    for line in lines:
        assert len(line) == len(close)
        assert all(value is None or math.isfinite(value) for value in line)


def test_indicator_service_calculates_every_available_catalog_item() -> None:
    candles = [
        Candle(
            timestamp=1_700_000_000_000 + index * 60_000,
            open=100 + index * 0.1,
            high=102 + index * 0.1,
            low=99 + index * 0.1,
            close=101 + index * 0.1,
            volume=10 + index,
            is_closed=True,
        )
        for index in range(200)
    ]
    selections = [
        IndicatorSelection(
            instance_id=f"test-{definition.id}",
            indicator_id=definition.id,
            placement=definition.placement,
            parameters={parameter.key: parameter.default for parameter in definition.parameters},
        )
        for definition in CATALOG.items
        if definition.available
    ]
    outputs = IndicatorService().calculate(candles, selections)
    assert len(outputs) == len(selections)
    assert all(len(plot.values) == len(candles) for output in outputs for plot in output.plots)


def test_indicator_service_calculates_period_lines_independently() -> None:
    candles = [
        Candle(
            timestamp=1_700_000_000_000 + index * 60_000,
            open=100 + index,
            high=103 + index,
            low=99 + index,
            close=102 + index,
            volume=10 + index,
            is_closed=True,
        )
        for index in range(40)
    ]
    selection = IndicatorSelection(
        instance_id="ma-default",
        indicator_id="ma",
        placement="main",
        parameters={
            "lines": [
                {"slot": 1, "period": 7, "source": "close"},
                {"slot": 3, "period": 12, "source": "open"},
            ]
        },
    )

    output = IndicatorService().calculate(candles, [selection])[0]

    assert [plot.key for plot in output.plots] == ["ma_1", "ma_3"]
    assert [plot.label for plot in output.plots] == ["MA(7)", "MA(12)"]
    assert output.plots[0].values[-1] == sma([bar.close for bar in candles], 7)[-1]
    assert output.plots[1].values[-1] == sma([bar.open for bar in candles], 12)[-1]
