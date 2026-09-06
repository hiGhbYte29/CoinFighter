# CoinFighter 迁移说明

## 迁移范围

旧项目 `/home/highbyte29/CoinFighter` 的本地研究能力已迁入 FastAPI 架构。迁移遵循
`docs/architecture.md` 的当前范围，不包含用户系统和实盘交易。

| 旧版能力 | 新位置 | 迁移结果 |
| --- | --- | --- |
| PyQt6 GUI | `frontend/` | 改为 Vue 3 浏览器 GUI |
| CCXT 历史数据源 | `app/infrastructure/providers/` | 改为异步 CCXT Provider |
| CCXT 行情快照 | `app/modules/market/` | 通过 REST API 和本地 WebSocket 提供 |
| CSV 数据集 | `local_data/market/` | 转换为按月分区的 Parquet |
| CSV 元数据 | `local_data/catalog/datasets.json` | 改为可重建的本地 Catalog |
| SMA Cross | `strategies/examples/sma_cross.py` | 迁移为新的 Strategy/Context 协议 |
| MACD Cross | `strategies/examples/macd_cross.py` | 迁移为新的 Strategy/Context 协议 |
| 回测引擎 | `app/modules/backtest/` | 改为子进程任务和文件化报告 |
| Matplotlib/Qt 图表 | `frontend/src/components/` | 改为 ECharts K 线与净值图 |

## 已迁移数据

旧版两份存在覆盖关系的 Binance USD-M ETH 日线 CSV 已合并去重为一个数据集：

```text
dataset_id: binanceusdm_swap_ethusdtusdt_1d
symbol: ETH/USDT:USDT
timeframe: 1d
range: 2020-01-01 至 2026-09-01
rows: 2,436
```

生成文件位于：

```text
local_data/market/binanceusdm/swap/ETHUSDTUSDT/1d/
```

本地行情和回测目录已加入 `.gitignore`，数据保留在当前机器，但不会被误提交为源码。

## 行为差异

- 新版策略通过 `StrategyContext` 产生模拟买卖信号，不再返回 `-1/0/1` 目标仓位。
- 根据第一版架构范围，回测采用现货多头模型；旧版 SMA/MACD 的做空信号在新版中解释为清仓。
- 当前信号在下一根 K 线开盘成交，显式避免使用当前 K 线收盘后无法获得的成交价格。
- 实时行情 WebSocket 第一版由后端轮询 CCXT 公共 REST 后向浏览器推送；以后可以在
  Provider 内替换为交易所原生 WebSocket，而不修改 GUI。
- 旧版 Matplotlib 和 PyQt6 代码没有复制到新项目，相关展示由浏览器端 ECharts 替代。

## 再次执行数据迁移

迁移脚本支持重复运行，Parquet 存储会按时间戳合并和去重：

```bash
.venv/bin/python scripts/migrate_legacy_data.py /home/highbyte29/CoinFighter/dataSets
```
