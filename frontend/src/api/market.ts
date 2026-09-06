import type { Candle, Ticker } from "@/types/api";
import { API_PREFIX, api, query } from "./client";

export const getProviders = () => api<Array<{ id: string; name: string; mode: string }>>("/market/providers");
export const getSymbols = (provider: string, marketType = "spot") =>
  api<string[]>(`/market/symbols?${query({ provider, market_type: marketType })}`);
export const getTicker = (provider: string, symbol: string, marketType = "spot") =>
  api<Ticker>(`/market/ticker?${query({ provider, symbol, market_type: marketType })}`);
export const getCandles = (provider: string, symbol: string, timeframe: string, limit = 200) =>
  api<Candle[]>(`/market/candles?${query({ provider, symbol, timeframe, limit })}`);

export function tickerSocketUrl(provider: string, symbol: string): string {
  const protocol = location.protocol === "https:" ? "wss:" : "ws:";
  return `${protocol}//${location.host}${API_PREFIX}/market/ws?${query({ provider, symbol })}`;
}
