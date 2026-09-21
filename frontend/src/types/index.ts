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
  task_type: string | null;
  target_name: string | null;
  training_start: string;
  training_end: string;
  evaluation_start: string;
  evaluation_end: string;
  test_start_date: string | null;
  test_end_date: string | null;
  parameters: Record<string, any> | null;
  random_state: number | null;
  feature_count: number | null;
  artifact_path: string | null;
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

export interface SentimentResponse {
  symbol: string;
  date: string;
  sentiment_score: number;
  sentiment_label: string;
  source: string;
  details: Record<string, any> | null;
}

export interface ExplainabilityResponse {
  model_run_id: number;
  model_name: string;
  task_type: string;
  prediction_date: string;
  predicted_class: number | null;
  predicted_return: number | null;
  predicted_direction: string | null;
  top_features: Array<{
    feature: string;
    shap_value: number;
  }>;
  feature_importance: Record<string, number>;
}
