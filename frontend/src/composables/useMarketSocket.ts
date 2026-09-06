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
    socket = new WebSocket(tickerSocketUrl(provider, symbol));
    socket.onopen = () => { connected.value = true; };
    socket.onmessage = (event) => {
      const payload = JSON.parse(event.data) as Ticker;
      if (payload.symbol) onTicker(payload);
    };
    socket.onclose = () => {
      connected.value = false;
      if (desired) reconnectTimer = window.setTimeout(() => connect(provider, symbol), 2000);
    };
  }
  function disconnect() {
    desired = false;
    connected.value = false;
    if (reconnectTimer) window.clearTimeout(reconnectTimer);
    socket?.close();
    socket = null;
  }
  onBeforeUnmount(disconnect);
  return { connected, connect, disconnect };
}
