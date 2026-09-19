import axios from 'axios';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export const api = axios.create({
  baseURL: `${API_BASE}/api`,
  headers: {
    'Content-Type': 'application/json',
  },
});

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

export interface MLDatasetPrepareResponse {
  symbol: string;
  start_date: string;
  end_date: string;
  original_rows: number;
  rows_after_cleaning: number;
  rows_removed: number;
  feature_count: number;
  feature_names: string[];
  target_names: string[];
  train_rows: number;
  validation_rows: number;
  test_rows: number;
  train_start_date: string | null;
  train_end_date: string | null;
  validation_start_date: string | null;
  validation_end_date: string | null;
  test_start_date: string | null;
  test_end_date: string | null;
  train_ratio: number;
  validation_ratio: number;
  test_ratio: number;
  leakage_safe: boolean;
  quality_issues: string[];
  X_train_shape: number[];
  X_validation_shape: number[];
  X_test_shape: number[];
}

export interface ModelTrainResponse {
  model_run_id: number;
  model_name: string;
  task_type: string;
  symbol: string;
  target_name: string;
  feature_names: string[];
  feature_count: number;
  parameters: Record<string, any>;
  random_state: number;
  training_rows: number;
  validation_rows: number;
  test_rows: number;
  training_start_date: string | null;
  training_end_date: string | null;
  validation_start_date: string | null;
  validation_end_date: string | null;
  test_start_date: string | null;
  test_end_date: string | null;
  training_completed: boolean;
  train_prediction_shape: number[];
  validation_prediction_shape: number[];
  test_prediction_shape: number[];
  artifact_path: string | null;
}

export interface ClassificationEvaluationResponse {
  model_run_id: number;
  model_name: string;
  task_type: string;
  split: string;
  sample_count: number;
  accuracy: number | null;
  precision: number | null;
  recall: number | null;
  f1: number | null;
  roc_auc: number | null;
  confusion_matrix: {
    true_negative: number;
    false_positive: number;
    false_negative: number;
    true_positive: number;
  } | null;
  class_distribution: {
    class_0_count: number;
    class_1_count: number;
    class_0_percentage: number;
    class_1_percentage: number;
  } | null;
  baseline: {
    strategy: string;
    predicted_class: number;
    accuracy: number;
    count: number;
    total: number;
  } | null;
}

export interface RegressionEvaluationResponse {
  model_run_id: number;
  model_name: string;
  task_type: string;
  split: string;
  sample_count: number;
  mae: number | null;
  rmse: number | null;
  r2: number | null;
  baseline: {
    strategy: string;
    predicted_value: number;
    mae: number;
  } | null;
}

export interface ClassificationPredictionResponse {
  model_run_id: number;
  model_name: string;
  task_type: string;
  symbol: string;
  prediction_date: string;
  target_name: string;
  predicted_class: number;
  predicted_direction: string;
  probability_down: number | null;
  probability_up: number | null;
}

export interface RegressionPredictionResponse {
  model_run_id: number;
  model_name: string;
  task_type: string;
  symbol: string;
  prediction_date: string;
  target_name: string;
  predicted_return: number;
}

export interface StatisticsAnalyzeResponse {
  symbol: string;
  date_range: string;
  sample_size: number;
  descriptive_statistics: Array<{
    feature: string;
    count: number;
    mean: number;
    median: number;
    std: number;
    min: number;
    max: number;
  }>;
  correlations: Array<{
    feature: string;
    target: string;
    method: string;
    correlation: number;
    p_value: number;
    sample_size: number;
    adjusted_p_value: number | null;
    significant_at_0_05: boolean | null;
  }>;
  lag_analysis: Array<{
    feature: string;
    target: string;
    correlation: number;
    p_value: number;
    sample_size: number;
  }>;
  direction_analysis: Record<string, Array<{
    feature: string;
    count: number;
    mean: number;
    median: number;
    std: number;
  }>>;
}

export const fetchDashboardSummary = async (symbol: string): Promise<DashboardSummary> => {
  const { data } = await api.get('/dashboard/summary', { params: { symbol } });
  return data;
};

export const fetchSearchTerms = async (): Promise<SearchTerm[]> => {
  const { data } = await api.get('/search-terms/', { params: { active_only: true } });
  return data;
};

export const fetchMarketData = async (symbol: string, startDate: string, endDate: string): Promise<MarketDataPoint[]> => {
  const { data } = await api.get('/market-data/', { params: { symbol, start_date: startDate, end_date: endDate } });
  return data;
};

export const fetchTrends = async (searchTermId: number, startDate: string, endDate: string): Promise<TrendDataPoint[]> => {
  const { data } = await api.get('/trends/', { params: { search_term_id: searchTermId, start_date: startDate, end_date: endDate } });
  return data;
};

export const fetchModelRuns = async (symbol?: string): Promise<ModelRun[]> => {
  const { data } = await api.get('/models/', { params: symbol ? { symbol } : {} });
  return data;
};

export const trainModel = async (payload: { symbol: string; start_date: string; end_date: string; task: string; model_name: string }): Promise<ModelTrainResponse> => {
  const { data } = await api.post('/models/train', payload);
  return data;
};

export const evaluateModel = async (payload: { model_run_id: number; evaluation_split: string }): Promise<ClassificationEvaluationResponse | RegressionEvaluationResponse> => {
  const { data } = await api.post('/models/evaluate', payload);
  return data;
};

export const predict = async (payload: { model_run_id: number; symbol: string; prediction_date: string }): Promise<ClassificationPredictionResponse | RegressionPredictionResponse> => {
  const { data } = await api.post('/models/predict', payload);
  return data;
};

export const prepareMLDataset = async (payload: { symbol: string; start_date: string; end_date: string; train_ratio?: number; validation_ratio?: number; test_ratio?: number }): Promise<MLDatasetPrepareResponse> => {
  const { data } = await api.post('/ml-dataset/prepare', payload);
  return data;
};

export const analyzeStatistics = async (payload: { symbol: string; start_date: string; end_date: string }): Promise<StatisticsAnalyzeResponse> => {
  const { data } = await api.post('/statistics/analyze', payload);
  return data;
};
