import type { TaskRecord } from "@/types/api";
import { api } from "./client";

export interface BacktestRequest {
  strategy: string;
  dataset_id: string;
  initial_cash: number;
  fee_rate: number;
  slippage: number;
  parameters: Record<string, unknown>;
}

export const listBacktests = () => api<TaskRecord[]>("/backtests");
export const createBacktest = (request: BacktestRequest) =>
  api<TaskRecord>("/backtests", { method: "POST", body: JSON.stringify(request) });
export const getBacktestTrades = (runId: string) => api<Array<Record<string, number | string>>>(`/backtests/${encodeURIComponent(runId)}/trades`);
export const getBacktestEquity = (runId: string) => api<Array<Record<string, number>>>(`/backtests/${encodeURIComponent(runId)}/equity`);
