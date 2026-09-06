import { onBeforeUnmount, ref } from "vue";

import { tickerSocketUrl } from "@/api/market";
import type { Ticker } from "@/types/api";

export function useMarketSocket(onTicker: (ticker: Ticker) => void) {
  const connected = ref(false);
  let socket: WebSocket | null = null;
  let reconnectTimer: number | undefined;
  let desired = false;
  function connect(provider: string, symbol: string) {
    disconnect();
    desired = true;
    const current = new WebSocket(tickerSocketUrl(provider, symbol));
    socket = current;
    current.onopen = () => {
      if (socket === current) connected.value = true;
    };
    current.onmessage = (event) => {
      if (socket !== current) return;
      const payload = JSON.parse(event.data) as Ticker;
      if (payload.symbol) onTicker(payload);
    };
    current.onclose = () => {
      if (socket !== current) return;
      connected.value = false;
      socket = null;
      if (desired) reconnectTimer = window.setTimeout(() => connect(provider, symbol), 2000);
    };
  }
  function disconnect() {
    desired = false;
    connected.value = false;
    if (reconnectTimer) window.clearTimeout(reconnectTimer);
    const current = socket;
    socket = null;
    current?.close();
  }
  onBeforeUnmount(disconnect);
  return { connected, connect, disconnect };
}
