import axios from 'axios';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export const api = axios.create({
  baseURL: `${API_BASE}/api`,
  headers: {
    'Content-Type': 'application/json',
  },
});

export interface SearchTermPayload {
  term: string;
  category?: string;
}

export interface MarketDataQuery {
  symbol: string;
  start_date: string;
  end_date: string;
}

export interface TrainModelPayload {
  model_name: string;
  symbol: string;
  target: string;
  training_start: string;
  training_end: string;
  evaluation_end: string;
}
