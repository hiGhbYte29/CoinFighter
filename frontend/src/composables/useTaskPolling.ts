import { onBeforeUnmount } from "vue";

export function useTaskPolling(callback: () => Promise<void>, intervalMs = 1500) {
  let timer: number | undefined;
  function start() {
    stop();
    void callback();
    timer = window.setInterval(() => void callback(), intervalMs);
  }
  function stop() {
    if (timer) window.clearInterval(timer);
    timer = undefined;
  }
  onBeforeUnmount(stop);
  return { start, stop };
}
