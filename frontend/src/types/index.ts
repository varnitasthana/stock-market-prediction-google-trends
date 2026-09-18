export interface SearchTerm {
  id: number;
  term: string;
  category: string;
  active: boolean;
  created_at: string;
}

export interface MarketDataPoint {
  id: number;
  symbol: string;
  date: string;
  open: number | null;
  high: number | null;
  low: number | null;
  close: number | null;
  adj_close: number | null;
  volume: number | null;
  daily_return: number | null;
  volatility: number | null;
}

export interface TrendDataPoint {
  id: number;
  search_term_id: number;
  date: string;
  interest_score: number | null;
}

export interface ModelRun {
  id: number;
  model_name: string;
  symbol: string;
  training_start: string;
  training_end: string;
  evaluation_start: string;
  evaluation_end: string;
  metrics: Record<string, any> | null;
  created_at: string;
}

export interface Prediction {
  id: number;
  model_run_id: number;
  symbol: string;
  prediction_date: string;
  predicted_return: number | null;
  predicted_direction: number | null;
  probability: number | null;
  actual_return: number | null;
  actual_direction: number | null;
  created_at: string;
}

export interface DashboardSummary {
  symbol: string;
  latest_close: number | null;
  latest_date: string | null;
  latest_daily_return: number | null;
  latest_model: string | null;
  last_training_date: string | null;
  prediction_direction: number | null;
  prediction_probability: number | null;
  prediction_date: string | null;
}
