<script setup lang="ts">
import { onMounted, ref, watch } from "vue";

import { getProviders, getSymbols } from "@/api/market";
import MarketChart from "@/components/market/MarketChart.vue";
import { useMarketSocket } from "@/composables/useMarketSocket";
import { useMarketStore } from "@/stores/market";
import { useSettingsStore } from "@/stores/settings";

const settings = useSettingsStore();
const market = useMarketStore();
const providers = ref<Array<{ id: string; name: string }>>([]);
const symbols = ref<string[]>([settings.symbol]);
const { connected, connect } = useMarketSocket((ticker) => { market.ticker = ticker; });

async function reload() {
  settings.persist();
  symbols.value = await getSymbols(settings.provider);
  if (!symbols.value.includes(settings.symbol)) settings.symbol = symbols.value[0] || "BTC/USDT";
  await market.load(settings.provider, settings.symbol, settings.timeframe);
  connect(settings.provider, settings.symbol);
}
onMounted(async () => { providers.value = await getProviders(); await reload(); });
watch(() => [settings.provider, settings.symbol, settings.timeframe], () => void reload());
const number = (value: number | null | undefined, digits = 2) => value == null ? "—" : value.toLocaleString(undefined, { maximumFractionDigits: digits });
</script>

<template>
  <div class="control-bar">
    <label>数据源<select v-model="settings.provider"><option v-for="item in providers" :key="item.id" :value="item.id">{{ item.name }}</option></select></label>
    <label>交易对<select v-model="settings.symbol"><option v-for="item in symbols" :key="item">{{ item }}</option></select></label>
    <label>周期<select v-model="settings.timeframe"><option v-for="item in ['1m','5m','15m','1h','4h','1d']" :key="item">{{ item }}</option></select></label>
    <span class="connection-pill" :class="{ online: connected }"><i></i>{{ connected ? "实时连接" : "正在连接" }}</span>
  </div>
  <div v-if="market.error" class="notice error">{{ market.error }}</div>
  <section class="ticker-strip">
    <article><span>最新价格</span><strong>{{ number(market.ticker?.last) }}</strong><em :class="{ negative: (market.ticker?.change_percent || 0) < 0 }">{{ number(market.ticker?.change_percent) }}%</em></article>
    <article><span>24H 高 / 低</span><strong>{{ number(market.ticker?.high) }}</strong><em class="neutral">{{ number(market.ticker?.low) }}</em></article>
    <article><span>24H 成交量</span><strong>{{ number(market.ticker?.base_volume, 4) }}</strong><em class="neutral">{{ settings.symbol.split('/')[0] }}</em></article>
  </section>
  <article class="panel chart-panel">
    <div class="panel-heading"><div><p class="eyebrow">{{ settings.provider.toUpperCase() }} · SPOT</p><h2>{{ settings.symbol }}</h2></div><span class="badge">{{ settings.timeframe }}</span></div>
    <div class="price-row"><strong>{{ number(market.ticker?.last) }}</strong><span>{{ number(market.ticker?.change_percent) }}%</span></div>
    <MarketChart :candles="market.candles" />
  </article>
</template>
