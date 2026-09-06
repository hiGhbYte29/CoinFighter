import { onBeforeUnmount, ref } from "vue";

import { chartSocketUrl } from "@/api/indicators";
import type { ChartDataRequest, ChartStreamMessage } from "@/types/api";

export function useChartSocket(onData: (message: ChartStreamMessage) => void) {
  const connected = ref(false);
  const error = ref("");
  let socket: WebSocket | null = null;
  let reconnectTimer: number | undefined;
  let desiredRequest: ChartDataRequest | null = null;

  function connect(request: ChartDataRequest) {
    disconnect(false);
    desiredRequest = request;
    error.value = "";
    const current = new WebSocket(chartSocketUrl());
    socket = current;
    current.onopen = () => {
      if (socket !== current || !desiredRequest) return;
      connected.value = true;
      current.send(JSON.stringify(desiredRequest));
    };
    current.onmessage = (event) => {
      const message = JSON.parse(event.data) as ChartStreamMessage;
      if (message.type === "error") error.value = message.message || "实时图表连接失败";
      else onData(message);
    };
    current.onclose = () => {
      if (socket !== current) return;
      connected.value = false;
      socket = null;
      if (desiredRequest) reconnectTimer = window.setTimeout(() => connect(desiredRequest!), 1500);
    };
    current.onerror = () => { error.value = "实时图表连接失败，正在重试"; };
  }

  function disconnect(clearDesired = true) {
    if (clearDesired) desiredRequest = null;
    connected.value = false;
    if (reconnectTimer) window.clearTimeout(reconnectTimer);
    reconnectTimer = undefined;
    const current = socket;
    socket = null;
    current?.close();
  }

  onBeforeUnmount(() => disconnect());
  return { connected, error, connect, disconnect };
}
