<script setup lang="ts">
import { computed, onMounted, reactive, ref } from "vue";

import { createBacktest, getBacktestEquity, getBacktestTrades, listBacktests } from "@/api/backtests";
import { listDatasets } from "@/api/datasets";
import { listStrategies } from "@/api/strategies";
import EquityChart from "@/components/backtests/EquityChart.vue";
import { useTaskPolling } from "@/composables/useTaskPolling";
import type { Dataset, StrategyInfo, TaskRecord } from "@/types/api";

const datasets = ref<Dataset[]>([]);
const strategies = ref<StrategyInfo[]>([]);
const runs = ref<TaskRecord[]>([]);
const selected = ref<TaskRecord>();
const equity = ref<Array<Record<string, number>>>([]);
const trades = ref<Array<Record<string, number | string>>>([]);
const form = reactive({ strategy: "", dataset_id: "", initial_cash: 100000, fee_rate: 0.001, slippage: 0.0002, parameters: "{}" });
const metrics = computed(() => (selected.value?.result?.metrics || {}) as Record<string, number | null>);

async function refresh() {
  runs.value = await listBacktests();
  if (selected.value) {
    const current = runs.value.find((run) => run.task_id === selected.value?.task_id);
    if (current) {
      const justCompleted = selected.value.status !== "COMPLETED" && current.status === "COMPLETED";
      selected.value = current;
      if (justCompleted) await select(current);
    }
  }
}
const polling = useTaskPolling(refresh, 1500);
async function select(run: TaskRecord) {
  selected.value = run;
  if (run.status === "COMPLETED") {
    [equity.value, trades.value] = await Promise.all([getBacktestEquity(run.task_id), getBacktestTrades(run.task_id)]);
  } else { equity.value = []; trades.value = []; }
}
async function submit() {
  const run = await createBacktest({ ...form, parameters: JSON.parse(form.parameters || "{}") });
  await refresh();
  await select(run);
}
const percent = (value: number | null | undefined) => value == null ? "—" : `${(value * 100).toFixed(2)}%`;
onMounted(async () => {
  [datasets.value, strategies.value] = await Promise.all([listDatasets(), listStrategies()]);
  form.dataset_id = datasets.value[0]?.dataset_id || "";
  form.strategy = strategies.value.find((item) => item.valid)?.name || "";
  polling.start();
});
</script>

<template>
  <section class="split-grid backtest-top">
    <article class="panel form-panel">
      <div class="panel-heading"><div><p class="eyebrow">NEW RUN</p><h2>配置回测</h2></div><span class="badge">NEXT OPEN</span></div>
      <form class="form-grid" @submit.prevent="submit">
        <label>策略<select v-model="form.strategy" required><option v-for="item in strategies.filter(s => s.valid)" :key="item.name" :value="item.name">{{ item.name }}</option></select></label>
        <label>数据集<select v-model="form.dataset_id" required><option v-for="item in datasets" :key="item.dataset_id" :value="item.dataset_id">{{ item.symbol }} · {{ item.timeframe }}</option></select></label>
        <label>初始资金<input v-model.number="form.initial_cash" type="number" min="1" /></label>
        <label>手续费率<input v-model.number="form.fee_rate" type="number" step="0.0001" min="0" /></label>
        <label>滑点<input v-model.number="form.slippage" type="number" step="0.0001" min="0" /></label>
        <label>策略参数 JSON<input v-model="form.parameters" /></label>
        <button class="primary-button form-submit" :disabled="!form.dataset_id || !form.strategy">启动回测</button>
      </form>
    </article>
    <article class="panel task-panel">
      <div class="panel-heading"><div><p class="eyebrow">RUN HISTORY</p><h2>历史任务</h2></div><span class="count">{{ runs.length }}</span></div>
      <div v-if="!runs.length" class="empty-state">下载数据后即可创建回测</div>
      <button v-for="run in runs.slice(0, 6)" :key="run.task_id" class="run-item" :class="{ active: selected?.task_id === run.task_id }" @click="select(run)">
        <span><strong>{{ String(run.request.strategy || 'BACKTEST') }}</strong><small>{{ run.message }}</small></span><em :class="run.status.toLowerCase()">{{ run.status }}</em>
      </button>
    </article>
  </section>
  <template v-if="selected">
    <section class="metric-grid">
      <article><span>总收益</span><strong>{{ percent(metrics.total_return) }}</strong></article>
      <article><span>最大回撤</span><strong>{{ percent(metrics.max_drawdown) }}</strong></article>
      <article><span>夏普比率</span><strong>{{ metrics.sharpe_ratio?.toFixed(2) || '—' }}</strong></article>
      <article><span>交易次数</span><strong>{{ metrics.trade_count ?? '—' }}</strong></article>
    </section>
    <article class="panel result-panel"><div class="panel-heading"><div><p class="eyebrow">EQUITY CURVE</p><h2>资金曲线</h2></div><span class="badge">{{ selected.status }}</span></div><EquityChart :rows="equity" /></article>
    <article class="panel table-panel"><div class="panel-heading"><div><p class="eyebrow">TRADES</p><h2>模拟成交</h2></div><span class="count">{{ trades.length }}</span></div><div v-if="!trades.length" class="empty-state">暂无成交记录</div><div v-else class="table-wrap"><table><thead><tr><th>时间</th><th>方向</th><th>价格</th><th>数量</th><th>手续费</th></tr></thead><tbody><tr v-for="(trade, index) in trades" :key="index"><td>{{ new Date(Number(trade.timestamp)).toLocaleString() }}</td><td>{{ trade.side }}</td><td>{{ Number(trade.price).toFixed(4) }}</td><td>{{ Number(trade.quantity).toFixed(6) }}</td><td>{{ Number(trade.fee).toFixed(4) }}</td></tr></tbody></table></div></article>
  </template>
</template>
