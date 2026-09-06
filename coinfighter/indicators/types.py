from dataclasses import dataclass

Series = list[float | None]


@dataclass(frozen=True)
class BollingerBands:
    upper: Series
    middle: Series
    lower: Series


@dataclass(frozen=True)
class MacdResult:
    macd: Series
    signal: Series
    histogram: Series


@dataclass(frozen=True)
class KdjResult:
    k: Series
    d: Series
    j: Series


@dataclass(frozen=True)
class StochRsiResult:
    k: Series
    d: Series


@dataclass(frozen=True)
class TrixResult:
    trix: Series
    signal: Series


@dataclass(frozen=True)
class SupertrendResult:
    value: Series
    direction: Series
