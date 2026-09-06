export interface Ticker {
  provider: string;
  market_type: string;
  symbol: string;
  timestamp: number | null;
  last: number | null;
  open: number | null;
  high: number | null;
  low: number | null;
  change_percent: number | null;
  base_volume: number | null;
}

export interface Candle {
  timestamp: number;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
  is_closed: boolean;
}

export interface Dataset {
  dataset_id: string;
  provider: string;
  market_type: string;
  symbol: string;
  timeframe: string;
  start: string;
  end: string;
  rows: number;
  updated_at: string;
  path: string;
}

export interface TaskRecord {
  task_id: string;
  run_id?: string;
  kind: string;
  status: string;
  progress: number;
  message: string;
  request: Record<string, unknown>;
  result: Record<string, unknown> | null;
  created_at: string;
  updated_at: string;
}

export interface StrategyInfo {
  name: string;
  class_name: string | null;
  description: string;
  default_parameters: Record<string, unknown>;
  source_path: string;
  editable: boolean;
  valid: boolean;
  errors: string[];
}

export interface StrategySource {
  name: string;
  source: string;
  valid: boolean;
  errors: string[];
}

export interface ApiFailure {
  code: string;
  message: string;
  details?: unknown;
}
