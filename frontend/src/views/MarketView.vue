<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue";
import { useRouter } from "vue-router";

import { getMarkets, getProviders } from "@/api/market";
import { useSettingsStore } from "@/stores/settings";
import type { MarketPage, MarketSortField, MarketSummary, SortOrder } from "@/types/api";

const router = useRouter();
const settings = useSettingsStore();
const providers = ref<Array<{ id: string; name: string }>>([]);
const marketPage = ref<MarketPage | null>(null);
const page = ref(1);
const pageSize = ref<20 | 30 | 50 | 100>(20);
const sortBy = ref<MarketSortField>("market_cap");
const sortOrder = ref<SortOrder>("desc");
const loading = ref(false);
const error = ref("");
let requestVersion = 0;

const visiblePages = computed(() => {
  const total = marketPage.value?.pages || 1;
  const result = new Set([1, total, page.value - 1, page.value, page.value + 1]);
  return [...result].filter((value) => value > 0 && value <= total).sort((a, b) => a - b);
});

async function loadMarkets() {
  const version = ++requestVersion;
  loading.value = true;
  error.value = "";
  try {
    const result = await getMarkets(
      settings.provider,
      page.value,
      pageSize.value,
      sortBy.value,
      sortOrder.value,
    );
    if (version !== requestVersion) return;
    marketPage.value = result;
    if (page.value > result.pages) page.value = result.pages;
  } catch (reason) {
    if (version !== requestVersion) return;
    error.value = reason instanceof Error ? reason.message : "行情列表加载失败";
  } finally {
    if (version === requestVersion) loading.value = false;
  }
}

function changeSort(field: MarketSortField) {
  if (sortBy.value === field) {
    sortOrder.value = sortOrder.value === "desc" ? "asc" : "desc";
  } else {
    sortBy.value = field;
    sortOrder.value = "desc";
  }
  page.value = 1;
}

function sortMark(field: MarketSortField) {
  if (sortBy.value !== field) return "↕";
  return sortOrder.value === "desc" ? "↓" : "↑";
}

function openMarket(item: MarketSummary) {
  settings.symbol = item.symbol;
  settings.persist();
  void router.push({
    name: "market-detail",
    params: { symbol: item.symbol.replace("/", "-") },
    query: { provider: settings.provider },
  });
}

function formatPrice(value: number | null) {
  if (value == null) return "—";
  const digits = value >= 1000 ? 2 : value >= 1 ? 4 : 8;
  return value.toLocaleString(undefined, { minimumFractionDigits: 0, maximumFractionDigits: digits });
}

function compactCurrency(value: number | null) {
  if (value == null) return "—";
  return new Intl.NumberFormat("zh-CN", {
    style: "currency",
    currency: "USD",
    notation: "compact",
    maximumFractionDigits: 2,
  }).format(value);
}

function colorFor(symbol: string) {
  const palette = ["#f7931a", "#627eea", "#26a17b", "#8247e5", "#14f195", "#2775ca"];
  return palette[[...symbol].reduce((sum, char) => sum + char.charCodeAt(0), 0) % palette.length];
}

function goToPage(value: number) {
  if (value < 1 || value > (marketPage.value?.pages || 1) || value === page.value) return;
  page.value = value;
}

onMounted(async () => {
  providers.value = await getProviders();
  await loadMarkets();
});

watch(() => settings.provider, () => {
  settings.persist();
  page.value = 1;
  void loadMarkets();
});
watch(page, () => void loadMarkets());
watch(pageSize, () => {
  page.value = 1;
  void loadMarkets();
});
watch([sortBy, sortOrder], () => void loadMarkets());
</script>

<template>
  <section class="market-list-panel">
    <div class="market-source-toolbar">
      <label class="exchange-select">
        <span>交易所</span>
        <select v-model="settings.provider" aria-label="选择交易所">
          <option v-for="item in providers" :key="item.id" :value="item.id">{{ item.name }}</option>
        </select>
      </label>
      <span>SPOT · USDT</span>
    </div>
    <div class="market-list-intro">
      <div>
        <h2>市值排名前列的代币</h2>
        <p>查看交易所现货代币的最新价格、24 小时涨跌、成交量与市值，点击任意代币进入深度行情。</p>
      </div>
    </div>

    <div v-if="error" class="notice error">
      <span>{{ error }}</span>
      <button class="text-button" type="button" @click="loadMarkets">重试</button>
    </div>

    <div class="market-table-wrap" :class="{ loading }" aria-live="polite">
      <table class="market-table">
        <thead>
          <tr>
            <th class="rank-column">#</th>
            <th>名称</th>
            <th class="number-column">
              <button type="button" @click="changeSort('price')">价格 <span>{{ sortMark("price") }}</span></button>
            </th>
            <th class="number-column">
              <button type="button" @click="changeSort('change')">24h 涨跌 <span>{{ sortMark("change") }}</span></button>
            </th>
            <th class="number-column">
              <button type="button" @click="changeSort('quote_volume')">24h 成交量 <span>{{ sortMark("quote_volume") }}</span></button>
            </th>
            <th class="number-column">
              <button type="button" @click="changeSort('market_cap')">市值 <span>{{ sortMark("market_cap") }}</span></button>
            </th>
            <th class="action-column">行情</th>
          </tr>
        </thead>
        <tbody v-if="loading && !marketPage">
          <tr v-for="index in 8" :key="index" class="skeleton-row">
            <td colspan="7"><span></span></td>
          </tr>
        </tbody>
        <tbody v-else>
          <tr
            v-for="(item, index) in marketPage?.items || []"
            :key="item.symbol"
            tabindex="0"
            @click="openMarket(item)"
            @keydown.enter="openMarket(item)"
          >
            <td class="rank-column">{{ (page - 1) * pageSize + index + 1 }}</td>
            <td>
              <div class="token-cell">
                <span class="token-logo" :style="{ background: colorFor(item.base) }">
                  <img v-if="item.image_url" :src="item.image_url" :alt="`${item.name} 图标`" @error="($event.currentTarget as HTMLImageElement).style.display = 'none'">
                  <b>{{ item.base.slice(0, 1) }}</b>
                </span>
                <span><strong>{{ item.base }}</strong><small>{{ item.name }}</small></span>
              </div>
            </td>
            <td class="number-column price-cell"><strong>${{ formatPrice(item.last) }}</strong><small>{{ item.symbol }}</small></td>
            <td class="number-column change-cell" :class="{ negative: (item.change_percent || 0) < 0 }">
              {{ item.change_percent == null ? "—" : `${item.change_percent >= 0 ? "+" : ""}${item.change_percent.toFixed(2)}%` }}
            </td>
            <td class="number-column">{{ compactCurrency(item.quote_volume) }}</td>
            <td class="number-column">{{ compactCurrency(item.market_cap) }}</td>
            <td class="action-column"><span class="chart-icon" aria-hidden="true">⌁</span><span class="order-icon" aria-hidden="true">▥</span></td>
          </tr>
          <tr v-if="!marketPage?.items.length">
            <td colspan="7" class="empty-market">当前交易所暂无可展示的 USDT 现货行情</td>
          </tr>
        </tbody>
      </table>
      <div v-if="loading && marketPage" class="table-loading"><span></span>正在刷新行情</div>
    </div>

    <div class="market-pagination">
      <p>共 {{ marketPage?.total || 0 }} 个交易对</p>
      <div class="page-controls">
        <button type="button" :disabled="page === 1" aria-label="上一页" @click="goToPage(page - 1)">‹</button>
        <template v-for="(value, index) in visiblePages" :key="value">
          <span v-if="index > 0 && value - visiblePages[index - 1] > 1">…</span>
          <button type="button" :class="{ active: value === page }" @click="goToPage(value)">{{ value }}</button>
        </template>
        <button type="button" :disabled="page >= (marketPage?.pages || 1)" aria-label="下一页" @click="goToPage(page + 1)">›</button>
      </div>
      <label class="page-size">每页
        <select v-model="pageSize">
          <option v-for="size in [20, 30, 50, 100]" :key="size" :value="size">{{ size }}</option>
        </select>
      </label>
    </div>
  </section>
</template>
