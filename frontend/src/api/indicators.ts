import type { ChartData, ChartDataRequest, IndicatorCatalog } from "@/types/api";
import { API_PREFIX, api } from "./client";

export const getIndicatorCatalog = () => api<IndicatorCatalog>("/indicators/catalog");

export const getChartData = (request: ChartDataRequest) => api<ChartData>("/market/chart-data", {
  method: "POST",
  body: JSON.stringify(request),
});

export function chartSocketUrl(): string {
  const protocol = location.protocol === "https:" ? "wss:" : "ws:";
  return `${protocol}//${location.host}${API_PREFIX}/market/chart/ws`;
}
