<script setup lang="ts">
import { onMounted, reactive, ref } from "vue";

import { downloadDataset, listDatasets, listDownloadTasks, validateDataset } from "@/api/datasets";
import { useTaskPolling } from "@/composables/useTaskPolling";
import type { Dataset, TaskRecord } from "@/types/api";

const now = new Date();
const monthAgo = new Date(now.getTime() - 30 * 86400000);
const localInput = (date: Date) => new Date(date.getTime() - date.getTimezoneOffset() * 60000).toISOString().slice(0, 16);
const form = reactive({ provider: "binance", market_type: "spot", symbol: "BTC/USDT", timeframe: "1h", start: localInput(monthAgo), end: localInput(now) });
const datasets = ref<Dataset[]>([]);
const tasks = ref<TaskRecord[]>([]);
const busy = ref(false);
const message = ref("");

async function refresh() { [datasets.value, tasks.value] = await Promise.all([listDatasets(), listDownloadTasks()]); }
const polling = useTaskPolling(refresh, 1200);
onMounted(() => polling.start());
async function submit() {
  busy.value = true; message.value = "";
  try {
    const task = await downloadDataset({ ...form, start: new Date(form.start).toISOString(), end: new Date(form.end).toISOString() });
    message.value = `下载任务 ${task.task_id} 已提交`;
    await refresh();
  } catch (error) { message.value = error instanceof Error ? error.message : "提交失败"; }
  finally { busy.value = false; }
}
</script>

<template>
  <section class="split-grid">
    <article class="panel form-panel">
      <div class="panel-heading"><div><p class="eyebrow">DOWNLOAD</p><h2>获取历史 K 线</h2></div><span class="badge">PARQUET</span></div>
      <form class="form-grid" @submit.prevent="submit">
        <label>数据源<select v-model="form.provider"><option value="binance">Binance</option><option value="okx">OKX</option><option value="bybit">Bybit</option></select></label>
        <label>市场<select v-model="form.market_type"><option value="spot">现货</option></select></label>
        <label>交易对<input v-model="form.symbol" /></label>
        <label>周期<select v-model="form.timeframe"><option v-for="item in ['1m','5m','15m','1h','4h','1d']" :key="item">{{ item }}</option></select></label>
        <label>开始时间<input v-model="form.start" type="datetime-local" /></label>
        <label>结束时间<input v-model="form.end" type="datetime-local" /></label>
        <button class="primary-button form-submit" :disabled="busy">{{ busy ? "提交中…" : "开始下载" }}</button>
      </form>
      <p v-if="message" class="form-message">{{ message }}</p>
    </article>
    <article class="panel task-panel">
      <div class="panel-heading"><div><p class="eyebrow">TASKS</p><h2>下载队列</h2></div><span class="count">{{ tasks.length }}</span></div>
      <div v-if="!tasks.length" class="empty-state">还没有下载任务</div>
      <div v-for="task in tasks.slice(0, 5)" :key="task.task_id" class="task-row">
        <div><strong>{{ String(task.request.symbol || 'DATA') }}</strong><small>{{ task.message }}</small></div><span>{{ task.progress }}%</span>
        <div class="progress"><i :style="{ width: `${task.progress}%` }"></i></div>
      </div>
    </article>
  </section>
  <article class="panel table-panel">
    <div class="panel-heading"><div><p class="eyebrow">LOCAL LIBRARY</p><h2>本地数据集</h2></div><span class="count">{{ datasets.length }}</span></div>
    <div v-if="!datasets.length" class="empty-state large">暂无数据集。使用上方表单下载第一份行情数据。</div>
    <div v-else class="table-wrap"><table><thead><tr><th>数据集</th><th>范围</th><th>行数</th><th>更新</th><th></th></tr></thead><tbody>
      <tr v-for="item in datasets" :key="item.dataset_id"><td><strong>{{ item.symbol }}</strong><small>{{ item.provider }} · {{ item.timeframe }}</small></td><td>{{ new Date(item.start).toLocaleDateString() }} — {{ new Date(item.end).toLocaleDateString() }}</td><td>{{ item.rows.toLocaleString() }}</td><td>{{ new Date(item.updated_at).toLocaleString() }}</td><td><button class="text-button" @click="validateDataset(item.dataset_id)">校验</button></td></tr>
    </tbody></table></div>
  </article>
</template>
