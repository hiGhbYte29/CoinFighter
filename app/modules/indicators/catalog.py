from app.modules.indicators.schemas import IndicatorCatalog, IndicatorDefinition, IndicatorParameter

SOURCE = IndicatorParameter(
    key="source",
    label="价格源",
    type="select",
    default="close",
    options=[
        {"value": "close", "label": "收盘价"},
        {"value": "open", "label": "开盘价"},
        {"value": "high", "label": "最高价"},
        {"value": "low", "label": "最低价"},
    ],
)


def integer(key: str, label: str, default: int, maximum: int = 500) -> IndicatorParameter:
    return IndicatorParameter(
        key=key,
        label=label,
        type="integer",
        default=default,
        minimum=1,
        maximum=maximum,
    )


def number(
    key: str, label: str, default: float, minimum: float, maximum: float
) -> IndicatorParameter:
    return IndicatorParameter(
        key=key,
        label=label,
        type="number",
        default=default,
        minimum=minimum,
        maximum=maximum,
    )


def periods(default: list[int], max_items: int = 6) -> IndicatorParameter:
    return IndicatorParameter(
        key="periods",
        label="周期",
        type="integer_list",
        default=default,
        minimum=1,
        maximum=500,
        max_items=max_items,
    )


CATALOG = IndicatorCatalog(
    items=[
        IndicatorDefinition(
            id="ma",
            name="MA · 移动平均线",
            description="指定周期内收盘价的算术平均值。",
            placement="main",
            parameters=[periods([7, 25, 99]), SOURCE],
        ),
        IndicatorDefinition(
            id="ema",
            name="EMA · 指数移动平均线",
            description="对近期价格赋予更高权重的移动平均线。",
            placement="main",
            parameters=[periods([7, 25, 99]), SOURCE],
        ),
        IndicatorDefinition(
            id="wma",
            name="WMA · 加权移动平均线",
            description="按时间顺序线性加权的移动平均线。",
            placement="main",
            parameters=[periods([7, 25, 99]), SOURCE],
        ),
        IndicatorDefinition(
            id="boll",
            name="BOLL · 布林带",
            description="移动平均线及其上下标准差通道。",
            placement="main",
            parameters=[integer("period", "周期", 20), number("deviation", "标准差", 2, 0.1, 10)],
        ),
        IndicatorDefinition(
            id="vwap",
            name="VWAP · 成交量加权均价",
            description="基于 K 线典型价格计算的滚动近似 VWAP。",
            placement="main",
            parameters=[integer("period", "周期", 20)],
        ),
        IndicatorDefinition(
            id="sar",
            name="SAR · 抛物线转向",
            description="用于识别趋势方向和潜在转向点。",
            placement="main",
            parameters=[
                number("step", "步长", 0.02, 0.001, 1),
                number("maximum", "最大步长", 0.2, 0.01, 1),
            ],
        ),
        IndicatorDefinition(
            id="super",
            name="SUPER · Supertrend",
            description="基于 ATR 的趋势跟踪线。",
            placement="main",
            parameters=[
                integer("period", "ATR 周期", 10),
                number("multiplier", "倍数", 3, 0.1, 20),
            ],
        ),
        IndicatorDefinition(
            id="avl",
            name="AVL · 平均成交价",
            description="需要交易所提供累计成交额数据。",
            placement="main",
            available=False,
            unavailable_reason="当前标准 OHLCV 数据不包含精确成交额，暂不提供近似结果。",
        ),
        IndicatorDefinition(
            id="vol",
            name="VOL · 成交量",
            description="成交量柱及其移动平均线。",
            placement="sub",
            parameters=[periods([7, 14], max_items=2)],
        ),
        IndicatorDefinition(
            id="macd",
            name="MACD · 指数平滑异同平均线",
            description="快速与慢速 EMA 的差值、信号线和柱状图。",
            placement="sub",
            parameters=[
                integer("fast", "快速周期", 12),
                integer("slow", "慢速周期", 26),
                integer("signal", "信号周期", 9),
            ],
        ),
        IndicatorDefinition(
            id="rsi",
            name="RSI · 相对强弱指标",
            description="使用 Wilder 平滑衡量价格上涨和下跌动能。",
            placement="sub",
            parameters=[periods([6, 12, 24], max_items=3)],
        ),
        IndicatorDefinition(
            id="mfi",
            name="MFI · 资金流量指标",
            description="结合价格和成交量衡量资金流入与流出。",
            placement="sub",
            parameters=[integer("period", "周期", 14)],
        ),
        IndicatorDefinition(
            id="kdj",
            name="KDJ · 随机指标",
            description="根据一定周期内的最高、最低和收盘价计算 K、D、J。",
            placement="sub",
            parameters=[
                integer("period", "周期", 9),
                integer("smooth_k", "K 平滑", 3),
                integer("smooth_d", "D 平滑", 3),
            ],
        ),
        IndicatorDefinition(
            id="obv",
            name="OBV · 能量潮",
            description="根据价格方向累计成交量。",
            placement="sub",
        ),
        IndicatorDefinition(
            id="cci",
            name="CCI · 顺势指标",
            description="衡量典型价格偏离其移动平均值的程度。",
            placement="sub",
            parameters=[integer("period", "周期", 20)],
        ),
        IndicatorDefinition(
            id="stochrsi",
            name="StochRSI · 随机 RSI",
            description="对 RSI 再进行随机指标标准化。",
            placement="sub",
            parameters=[
                integer("rsi_period", "RSI 周期", 14),
                integer("stoch_period", "随机周期", 14),
                integer("smooth_k", "K 平滑", 3),
                integer("smooth_d", "D 平滑", 3),
            ],
        ),
        IndicatorDefinition(
            id="wr",
            name="WR · 威廉指标",
            description="衡量收盘价在近期最高价和最低价区间中的位置。",
            placement="sub",
            parameters=[integer("period", "周期", 14)],
        ),
        IndicatorDefinition(
            id="trix",
            name="TRIX · 三重指数平滑平均线",
            description="三重 EMA 的变化率及信号线。",
            placement="sub",
            parameters=[integer("period", "周期", 12), integer("signal", "信号周期", 9)],
        ),
    ]
)

DEFINITIONS = {item.id: item for item in CATALOG.items}
