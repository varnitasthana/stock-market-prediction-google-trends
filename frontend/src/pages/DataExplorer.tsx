import { useQuery } from '@tanstack/react-query';
import { fetchMarketData, fetchTrends, fetchSearchTerms } from '../services/api';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts';
import type { MarketDataPoint, TrendDataPoint, SearchTerm } from '../types/api';

const DEFAULT_SYMBOL = '^NSEI';
const DEFAULT_START = '2024-01-01';
const DEFAULT_END = '2026-09-21';

export default function DataExplorer() {
  const { data: marketData, isLoading: marketLoading, error: marketError } = useQuery({
    queryKey: ['marketData', DEFAULT_SYMBOL, DEFAULT_START, DEFAULT_END],
    queryFn: () => fetchMarketData(DEFAULT_SYMBOL, DEFAULT_START, DEFAULT_END),
  });

  const { data: terms } = useQuery({
    queryKey: ['searchTerms'],
    queryFn: fetchSearchTerms,
  });

  const activeTerm = terms?.[0];
  const { data: trendsData, isLoading: trendsLoading, error: trendsError } = useQuery({
    queryKey: ['trends', activeTerm?.id, DEFAULT_START, DEFAULT_END],
    queryFn: () => fetchTrends(activeTerm!.id, DEFAULT_START, DEFAULT_END),
    enabled: !!activeTerm,
  });

  const marketChartData = (marketData ?? []).map((d: MarketDataPoint) => ({
    date: d.date,
    close: d.close != null ? Number(d.close) : null,
    daily_return: d.daily_return != null ? Number(d.daily_return) : null,
  }));

  const trendsChartData = (trendsData ?? []).map((d: TrendDataPoint) => ({
    date: d.date,
    interest_score: d.interest_score ?? 0,
  }));

  return (
    <div className="space-y-6">
      <section>
        <h2 className="text-xl font-semibold text-gray-900">Market Data</h2>
        <p className="mt-1 text-sm text-gray-500">NIFTY 50 closing prices and daily returns</p>
        {marketLoading && <p className="mt-2 text-sm text-gray-600">Loading market data...</p>}
        {marketError && <p className="mt-2 text-sm text-red-600">Failed to load market data.</p>}
        {!marketLoading && !marketError && marketData && (
          <div className="mt-4 h-80 w-full rounded-lg border border-gray-200 bg-white p-4">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={marketChartData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="date" tick={{ fontSize: 12 }} />
                <YAxis tick={{ fontSize: 12 }} />
                <Tooltip />
                <Legend />
                <Line type="monotone" dataKey="close" stroke="#2563eb" name="Close" dot={false} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        )}
      </section>

      <section>
        <h2 className="text-xl font-semibold text-gray-900">Google Trends</h2>
        <p className="mt-1 text-sm text-gray-500">Relative search interest (0–100) for configured terms</p>
        {!activeTerm && <p className="mt-2 text-sm text-gray-600">No search terms configured.</p>}
        {trendsLoading && <p className="mt-2 text-sm text-gray-600">Loading trends...</p>}
        {trendsError && <p className="mt-2 text-sm text-red-600">Failed to load trends data.</p>}
        {!trendsLoading && !trendsError && trendsData && (
          <div className="mt-4 h-80 w-full rounded-lg border border-gray-200 bg-white p-4">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={trendsChartData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="date" tick={{ fontSize: 12 }} />
                <YAxis tick={{ fontSize: 12 }} domain={[0, 100]} />
                <Tooltip />
                <Legend />
                <Line type="monotone" dataKey="interest_score" stroke="#16a34a" name="Interest" dot={false} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        )}
      </section>
    </div>
  );
}
