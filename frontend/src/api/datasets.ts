import type { Candle, Dataset, TaskRecord } from "@/types/api";
import { api } from "./client";

export interface DownloadRequest {
  provider: string;
  market_type: string;
  symbol: string;
  timeframe: string;
  start: string;
  end: string;
}

export const listDatasets = () => api<Dataset[]>("/datasets");
export const listDownloadTasks = () => api<TaskRecord[]>("/datasets/tasks");
export const downloadDataset = (request: DownloadRequest) =>
  api<TaskRecord>("/datasets/download", { method: "POST", body: JSON.stringify(request) });
export const getDatasetCandles = (datasetId: string, limit = 1000) =>
  api<Candle[]>(`/datasets/${encodeURIComponent(datasetId)}/candles?limit=${limit}`);
export const validateDataset = (datasetId: string) =>
  api<Record<string, unknown>>(`/datasets/${encodeURIComponent(datasetId)}/validate`, { method: "POST" });
