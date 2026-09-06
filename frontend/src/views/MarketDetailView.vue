<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from "vue";
import { useRoute, useRouter } from "vue-router";

import { getOrderBook, getProviders } from "@/api/market";
import MarketChart from "@/components/market/MarketChart.vue";
import { useMarketSocket } from "@/composables/useMarketSocket";
import { useMarketStore } from "@/stores/market";
import { useSettingsStore } from "@/stores/settings";
import type { OrderBook, OrderBookLevel } from "@/types/api";

const route = useRoute();
const router = useRouter();
const settings = useSettingsStore();
const market = useMarketStore();
const providers = ref<Array<{ id: string; name: string }>>([]);
const orderBook = ref<OrderBook | null>(null);
const orderBookError = ref("");
const orderBookLoading = ref(false);
const allowedProviders = new Set(["binance", "okx", "bybit"]);
const routeProvider = typeof route.query.provider === "string" ? route.query.provider : "";
if (allowedProviders.has(routeProvider)) settings.provider = routeProvider;

const symbol = computed(() => String(route.params.symbol || "BTC-USDT").replace("-", "/").toUpperCase());
const baseAsset = computed(() => symbol.value.split("/")[0]);
const quoteAsset = computed(() => symbol.value.split("/")[1] || "USDT");
const { connected, connect } = useMarketSocket((ticker) => { market.ticker = ticker; });
let orderBookTimer: number | undefined;
let initialized = false;

const maxBookAmount = computed(() => Math.max(
  1,
  ...(orderBook.value?.asks || []).map((row) => row.amount),
  ...(orderBook.value?.bids || []).map((row) => row.amount),
));

const visibleAsks = computed(() => [...(orderBook.value?.asks || [])].slice(0, 10).reverse());
const visibleBids = computed(() => (orderBook.value?.bids || []).slice(0, 10));

function number(value: number | null | undefined, digits = 2) {
  if (value == null) return "—";
  return value.toLocaleString(undefined, { maximumFractionDigits: digits });
}

function precise(value: number | null | undefined) {
  if (value == null) return "—";
  const digits = value >= 1000 ? 2 : value >= 1 ? 4 : 8;
  return value.toLocaleString(undefined, { maximumFractionDigits: digits });
}

function depthWidth(level: OrderBookLevel) {
  return `${Math.max(3, (level.amount / maxBookAmount.value) * 100)}%`;
}

async function loadOrderBook(silent = false) {
  if (!silent) orderBookLoading.value = true;
  orderBookError.value = "";
  try {
    orderBook.value = await getOrderBook(settings.provider, symbol.value, 20);
  } catch (reason) {
    orderBookError.value = reason instanceof Error ? reason.message : "订单簿加载失败";
  } finally {
    orderBookLoading.value = false;
  }
}

async function reload() {
  settings.symbol = symbol.value;
  settings.persist();
  void router.replace({ query: { ...route.query, provider: settings.provider } });
  await Promise.all([
    market.load(settings.provider, symbol.value, settings.timeframe),
    loadOrderBook(),
  ]);
  connect(settings.provider, symbol.value);
}

onMounted(async () => {
  providers.value = await getProviders();
  initialized = true;
  await reload();
  orderBookTimer = window.setInterval(() => void loadOrderBook(true), 5000);
});

watch([() => settings.provider, () => settings.timeframe, symbol], () => {
  if (initialized) void reload();
});

onBeforeUnmount(() => {
  if (orderBookTimer) window.clearInterval(orderBookTimer);
});
</script>

<template>
  <div class="detail-toolbar">
    <RouterLink class="back-link" to="/">← 返回行情</RouterLink>
    <div class="detail-controls">
      <label>交易所
        <select v-model="settings.provider">
          <option v-for="item in providers" :key="item.id" :value="item.id">{{ item.name }}</option>
        </select>
      </label>
      <label>周期
        <select v-model="settings.timeframe">
          <option v-for="item in ['1m', '5m', '15m', '1h', '4h', '1d']" :key="item">{{ item }}</option>
        </select>
      </label>
      <span class="connection-pill" :class="{ online: connected }"><i></i>{{ connected ? "实时连接" : "正在连接" }}</span>
    </div>
  </div>

  <div v-if="market.error" class="notice error">{{ market.error }}</div>

  <section class="asset-heading">
    <div>
      <p class="eyebrow">{{ settings.provider.toUpperCase() }} · SPOT</p>
      <h2>{{ baseAsset }} <span>/ {{ quoteAsset }}</span></h2>
    </div>
    <div class="asset-price">
      <strong>${{ precise(market.ticker?.last) }}</strong>
      <span :class="{ negative: (market.ticker?.change_percent || 0) < 0 }">
        {{ market.ticker?.change_percent == null ? "—" : `${market.ticker.change_percent >= 0 ? "+" : ""}${number(market.ticker.change_percent)}%` }}
      </span>
    </div>
  </section>

  <section class="ticker-strip detail-ticker-strip">
    <article><span>24H 最高</span><strong>{{ precise(market.ticker?.high) }}</strong><em class="neutral">{{ quoteAsset }}</em></article>
    <article><span>24H 最低</span><strong>{{ precise(market.ticker?.low) }}</strong><em class="neutral">{{ quoteAsset }}</em></article>
    <article><span>24H 成交量</span><strong>{{ number(market.ticker?.base_volume, 4) }}</strong><em class="neutral">{{ baseAsset }}</em></article>
  </section>

  <div class="market-detail-grid">
    <article class="panel detail-chart-panel">
      <div class="panel-heading">
        <div><p class="eyebrow">PRICE & VOLUME</p><h2>K 线与成交量</h2></div>
        <span class="badge">{{ settings.timeframe }}</span>
      </div>
      <div v-if="market.loading && !market.candles.length" class="chart-placeholder">正在加载 K 线…</div>
      <MarketChart v-else :candles="market.candles" />
    </article>

    <article class="panel order-book-panel">
      <div class="panel-heading">
        <div><p class="eyebrow">MARKET DEPTH</p><h2>订单簿</h2></div>
        <span class="live-label"><i></i>实时</span>
      </div>
      <p v-if="orderBookError" class="order-error">{{ orderBookError }}</p>
      <div class="book-head"><span>价格 ({{ quoteAsset }})</span><span>数量 ({{ baseAsset }})</span></div>
      <div class="book-rows asks">
        <div v-for="(level, index) in visibleAsks" :key="`ask-${index}`" class="book-row">
          <i :style="{ width: depthWidth(level) }"></i><span>{{ precise(level.price) }}</span><span>{{ number(level.amount, 6) }}</span>
        </div>
      </div>
      <div class="book-mid">
        <strong>${{ precise(market.ticker?.last) }}</strong><span>最新成交价</span>
      </div>
      <div class="book-rows bids">
        <div v-for="(level, index) in visibleBids" :key="`bid-${index}`" class="book-row">
          <i :style="{ width: depthWidth(level) }"></i><span>{{ precise(level.price) }}</span><span>{{ number(level.amount, 6) }}</span>
        </div>
      </div>
      <div v-if="orderBookLoading && !orderBook" class="book-loading">正在加载订单簿…</div>
    </article>
  </div>
</template>
