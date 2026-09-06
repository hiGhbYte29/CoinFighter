import type { StrategyInfo, StrategySource } from "@/types/api";
import { api } from "./client";

export const listStrategies = () => api<StrategyInfo[]>("/strategies");
export const getStrategySource = (name: string) => api<StrategySource>(`/strategies/${encodeURIComponent(name)}/source`);
export const createStrategy = (name: string) =>
  api<StrategySource>("/strategies", { method: "POST", body: JSON.stringify({ name }) });
export const saveStrategy = (name: string, source: string) =>
  api<StrategySource>(`/strategies/${encodeURIComponent(name)}/source`, {
    method: "PUT",
    body: JSON.stringify({ source }),
  });
