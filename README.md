# CoinFighter FastAPI

CoinFighter 是一个本地优先的数字资产行情研究与策略回测工具。本版本将旧版 PyQt/CSV
项目迁移为 FastAPI + Vue 架构，使用 CCXT 获取公开行情，使用 Parquet 保存本地历史
数据，不包含登录、账户管理或实盘交易。

## 已实现功能

- Binance、OKX、Bybit 等 CCXT 公共行情适配。
- 最新价格、近期 K 线和本地 WebSocket 行情推送。
- 历史 OHLCV 分页下载、增量合并、月度 Parquet 分区和数据质量检查。
- 浏览器内创建、编辑和校验 Python 策略。
- 下一根 K 线开盘成交的现货多头回测，支持手续费和滑点。
- 本地保存回测配置、状态、成交、净值和汇总指标。
- Vue 3 GUI：实时看盘、数据管理、策略实验室和回测分析。
- 从旧版 CoinFighter CSV 数据集迁移到 Parquet 的脚本。

详细设计见 [架构文档](docs/architecture.md)。

## 安装

需要 Python 3.11+ 和 Node.js 20+。

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -e '.[dev]'

cd frontend
pnpm install
pnpm run build
cd ..
```

## 启动

前端构建完成后由 FastAPI 直接提供 GUI：

```bash
.venv/bin/uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```

打开：

- GUI：<http://127.0.0.1:8000>
- API 文档：<http://127.0.0.1:8000/api/v1/docs>

默认行情源是 Binance，也可在 GUI 中选择 OKX 或 Bybit。这些公开行情
请求不需要 API Key，但需要网络连接。

## 前端开发

分别运行后端和 Vite 开发服务器：

```bash
.venv/bin/uvicorn main:app --host 127.0.0.1 --port 8000 --reload
cd frontend
pnpm run dev
```

访问 <http://127.0.0.1:5173>。Vite 会把 `/api` 和 WebSocket 请求代理到 FastAPI。

## 迁移旧版数据

```bash
.venv/bin/python scripts/migrate_legacy_data.py /path/to/CoinFighter/dataSets
```

迁移脚本会读取旧版 CSV 及其 `*.meta.json`，按月份写入
`local_data/market/{provider}/{market_type}/{symbol}/{timeframe}`，并更新本地 Catalog。

当前工作区已迁移旧项目中的 Binance USD-M `ETH/USDT:USDT` 日线数据，共 2,436 根。

## 策略开发

用户策略位于 `strategies/user`，内置示例位于 `strategies/examples`。策略接收当前及以前
的 K 线，并通过 Context 产生模拟买卖信号：

```python
from app.modules.strategies.base import Bar, Strategy, StrategyContext


class ExampleStrategy(Strategy):
    name = "example_strategy"
    description = "示例策略"
    default_parameters = {"window": 20}

    def on_bar(self, context: StrategyContext, bar: Bar) -> None:
        closes = context.closes(int(context.parameters["window"]))
        if len(closes) < int(context.parameters["window"]):
            return
        if bar.close > sum(closes) / len(closes) and context.position == 0:
            context.buy()
        elif context.position > 0:
            context.close_position()
```

当前策略文件是本机可信 Python 代码，不是安全沙箱。

## 测试

```bash
.venv/bin/ruff check app strategies tests
.venv/bin/pytest
cd frontend && pnpm run build
```
