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

export type IndicatorPlacement = "main" | "sub";
export type IndicatorParameterType = "integer" | "number" | "integer_list" | "select";

export interface IndicatorParameter {
  key: string;
  label: string;
  type: IndicatorParameterType;
  default: unknown;
  minimum: number | null;
  maximum: number | null;
  max_items: number | null;
  options: Array<{ value: string; label: string }>;
}

export interface IndicatorDefinition {
  id: string;
  name: string;
  description: string;
  placement: IndicatorPlacement;
  parameters: IndicatorParameter[];
  available: boolean;
  unavailable_reason: string | null;
}

export interface IndicatorCatalog {
  formula_version: number;
  items: IndicatorDefinition[];
}

export interface IndicatorSelection {
  instance_id: string;
  indicator_id: string;
  placement: IndicatorPlacement;
  parameters: Record<string, unknown>;
}

export interface IndicatorGuide {
  value: number;
  label: string | null;
}

export interface IndicatorPlot {
  key: string;
  label: string;
  render_type: "line" | "bar" | "scatter";
  values: Array<number | null>;
  color: string;
}

export interface IndicatorOutput {
  instance_id: string;
  indicator_id: string;
  label: string;
  placement: IndicatorPlacement;
  plots: IndicatorPlot[];
  guides: IndicatorGuide[];
  axis_min: number | null;
  axis_max: number | null;
}

export interface ChartDataRequest {
  provider: string;
  market_type: string;
  symbol: string;
  timeframe: string;
  visible_limit: number;
  indicators: IndicatorSelection[];
}

export interface ChartData {
  formula_version: number;
  candles: Candle[];
  indicators: IndicatorOutput[];
}

export interface ChartStreamMessage {
  type: "snapshot" | "update" | "error";
  sequence?: number;
  last_price?: number | null;
  data?: ChartData;
  message?: string;
}

export interface MarketSummary {
  provider: string;
  symbol: string;
  base: string;
  quote: string;
  name: string;
  image_url: string | null;
  last: number | null;
  change_percent: number | null;
  base_volume: number | null;
  quote_volume: number | null;
  market_cap: number | null;
  market_cap_rank: number | null;
}

export interface MarketPage {
  provider: string;
  page: number;
  page_size: number;
  total: number;
  pages: number;
  sort_by: MarketSortField;
  sort_order: SortOrder;
  items: MarketSummary[];
}

export type MarketSortField = "market_cap" | "quote_volume" | "change" | "price";
export type SortOrder = "asc" | "desc";

export interface OrderBookLevel {
  price: number;
  amount: number;
}

export interface OrderBook {
  provider: string;
  market_type: string;
  symbol: string;
  timestamp: number | null;
  bids: OrderBookLevel[];
  asks: OrderBookLevel[];
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
