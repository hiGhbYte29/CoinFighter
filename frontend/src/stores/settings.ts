import { defineStore } from "pinia";
import { ref } from "vue";

export const useSettingsStore = defineStore("settings", () => {
  const supportedProviders = new Set(["binance", "okx", "bybit"]);
  const storedProvider = localStorage.getItem("cf-provider");
  const provider = ref(storedProvider && supportedProviders.has(storedProvider) ? storedProvider : "binance");
  const symbol = ref(localStorage.getItem("cf-symbol") || "BTC/USDT");
  const timeframe = ref(localStorage.getItem("cf-timeframe") || "1h");
  function persist() {
    localStorage.setItem("cf-provider", provider.value);
    localStorage.setItem("cf-symbol", symbol.value);
    localStorage.setItem("cf-timeframe", timeframe.value);
  }
  return { provider, symbol, timeframe, persist };
});
