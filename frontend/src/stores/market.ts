import { defineStore } from "pinia";
import { ref } from "vue";

import { getCandles, getTicker } from "@/api/market";
import type { Candle, Ticker } from "@/types/api";

export const useMarketStore = defineStore("market", () => {
  const ticker = ref<Ticker | null>(null);
  const candles = ref<Candle[]>([]);
  const loading = ref(false);
  const error = ref("");
  async function load(provider: string, symbol: string, timeframe: string) {
    loading.value = true;
    error.value = "";
    try {
      [ticker.value, candles.value] = await Promise.all([
        getTicker(provider, symbol),
        getCandles(provider, symbol, timeframe),
      ]);
    } catch (reason) {
      error.value = reason instanceof Error ? reason.message : "行情加载失败";
    } finally {
      loading.value = false;
    }
  }
  return { ticker, candles, loading, error, load };
});
