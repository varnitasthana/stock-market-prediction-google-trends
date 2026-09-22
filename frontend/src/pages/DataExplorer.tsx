import { useMemo, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts';
import { fetchMarketData, fetchTrends, fetchSearchTerms, fetchMarketDataStatus } from '../services/api';
import type { MarketDataPoint, TrendDataPoint, SearchTerm, MarketDataStatusResponse } from '../types/api';
import HelpPanel from '../components/HelpPanel';
import FeatureGlossary from '../components/FeatureGlossary';
import PageIntro from '../components/PageIntro';
import StatusBadge from '../components/StatusBadge';
import TrendInsights from '../components/TrendInsights';
import { formatDisplayDate, getTodayISO } from '../utils/date';

const DEFAULT_SYMBOL = '^NSEI';
const SAFE_START = '2024-01-01';
const MARKET_FEATURES = [
  'daily_return',
  'log_return',
  'volatility_5d',
  'return_lag_1',
  'return_lag_3',
  'return_lag_5',
];

function trendFeatures(term?: string): string[] {
  const prefix = term?.toLowerCase().replace(/ /g, '_').replace(/-/g, '_');
  if (!prefix) return [];
  return [
    `${prefix}_trend`,
    `${prefix}_trend_lag_1`,
    `${prefix}_trend_lag_3`,
    `${prefix}_trend_lag_7`,
    `${prefix}_trend_change`,
  ];
}

function StatusOverview({ status, loading }: { status?: MarketDataStatusResponse | null; loading: boolean }) {
  if (loading) {
    return (
      <div className="flex flex-wrap gap-2">
        <StatusBadge label="Checking market status" />
      </div>
    );
  }

  if (!status) {
    return (
      <div className="flex flex-wrap gap-2">
        <StatusBadge label="Using safe date defaults" tone="warning" />
      </div>
    );
  }

  return (
    <div className="flex flex-wrap gap-2">
      <StatusBadge label={`Today: ${formatDisplayDate(status.today)}`} />
      <StatusBadge label={`Expected Session: ${formatDisplayDate(status.expected_session)}`} tone={status.is_stale ? 'warning' : 'success'} />
      <StatusBadge label={`Latest Stored Session: ${formatDisplayDate(status.last_stored_date)}`} tone={status.is_stale ? 'warning' : 'success'} />
    </div>
  );
}

export default function DataExplorer() {
  const { data: marketStatus, isLoading: statusLoading, error: statusError } = useQuery({
    queryKey: ['marketStatus', DEFAULT_SYMBOL],
    queryFn: () => fetchMarketDataStatus(DEFAULT_SYMBOL),
  });

  const rangeStart = marketStatus?.first_stored_date ?? SAFE_START;
  const rangeEnd = marketStatus?.last_stored_date ?? marketStatus?.expected_session ?? getTodayISO();

  const { data: marketData, isLoading: marketLoading, error: marketError } = useQuery({
    queryKey: ['marketData', DEFAULT_SYMBOL, rangeStart, rangeEnd],
    queryFn: () => fetchMarketData(DEFAULT_SYMBOL, rangeStart, rangeEnd),
    enabled: !!marketStatus || !!statusError,
  });

  const { data: terms, isLoading: termsLoading, error: termsError } = useQuery({
    queryKey: ['searchTerms'],
    queryFn: fetchSearchTerms,
  });

  const [selectedTermId, setSelectedTermId] = useState<number | null>(null);

  const activeTerm = terms?.find((term: SearchTerm) => term.id === selectedTermId) ?? terms?.[0];

  const { data: trendsData, isLoading: trendsLoading, error: trendsError } = useQuery({
    queryKey: ['trends', activeTerm?.id, rangeStart, rangeEnd],
    queryFn: () => fetchTrends(activeTerm!.id, rangeStart, rangeEnd),
    enabled: !!activeTerm && (!!marketStatus || !!statusError),
  });

  const marketChartData = useMemo(() => (
    [...(marketData ?? [])]
      .sort((a, b) => a.date.localeCompare(b.date))
      .map((d: MarketDataPoint) => ({
        date: d.date,
        close: d.close != null ? Number(d.close) : null,
        daily_return: d.daily_return != null ? Number(d.daily_return) : null,
      }))
  ), [marketData]);

  const trendsChartData = useMemo(() => (
    [...(trendsData ?? [])]
      .sort((a, b) => a.date.localeCompare(b.date))
      .map((d: TrendDataPoint) => ({
        date: d.date,
        interest_score: d.interest_score != null ? Number(d.interest_score) : null,
      }))
  ), [trendsData]);

  const hasMarketData = (marketData?.length ?? 0) > 0;
  const hasTrendsData = (trendsData?.length ?? 0) > 0;

  return (
    <div className="space-y-6" aria-live="polite">
      <PageIntro
        title="Data Explorer"
        description="Inspect stored NIFTY 50 market history and Google Trends interest in the same historical window."
      >
        <StatusOverview status={marketStatus} loading={statusLoading} />
      </PageIntro>

      <HelpPanel title="How to read this page">
        <p><strong>Purpose:</strong> Compare market sessions with search-interest history before using the data in a model.</p>
        <p><strong>Inputs:</strong> A stored market symbol, a configured Google Trends term, and the available date range. Today and the Expected Session describe the calendar; Latest Stored Session is the newest row actually available.</p>
        <p><strong>Outputs:</strong> Closing-price and search-interest charts plus a short historical pattern summary.</p>
        <p><strong>Interpretation:</strong> Look for repeated movement across several sessions. A search spike and a market move happening together is a clue, not proof of cause and effect.</p>
        <p><strong>Limitations:</strong> Google Trends interest is a relative 0–100 score, and stored market rows can lag the expected session.</p>
        <p><strong>Historical patterns:</strong> Compare direction, volatility, positive versus negative sessions, and search-interest changes over the full window rather than focusing on one outlier.</p>
      </HelpPanel>

      {statusError && (
        <p role="alert" className="rounded-md border border-red-200 bg-red-50 p-3 text-sm text-red-700">
          Market status could not be loaded. Safe date defaults are being used. {String(statusError)}
        </p>
      )}

      {marketStatus?.message && (
        <div className="rounded-md border border-blue-200 bg-blue-50 p-4 text-sm text-blue-900">
          <p className="font-semibold">Stored data notice</p>
          <p className="mt-1">{marketStatus.message}</p>
        </div>
      )}

      <section className="rounded-lg border border-gray-200 bg-white p-5 shadow-sm">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <h3 className="text-lg font-semibold text-gray-900">Market Data</h3>
            <p className="mt-1 text-sm text-gray-600">
              Stored sessions from {formatDisplayDate(rangeStart)} to {formatDisplayDate(rangeEnd)}
            </p>
          </div>
          <StatusBadge label={`Latest Stored Session: ${formatDisplayDate(rangeEnd)}`} tone={marketStatus?.is_stale ? 'warning' : 'success'} />
        </div>

        {statusLoading && <p className="mt-4 text-sm text-gray-600">Checking stored market coverage...</p>}
        {marketLoading && <p className="mt-4 text-sm text-gray-600">Loading market data...</p>}
        {marketError && (
          <p role="alert" className="mt-4 rounded-md border border-red-200 bg-red-50 p-3 text-sm text-red-700">
            Failed to load market data. {String(marketError)}
          </p>
        )}
        {marketData !== undefined && !hasMarketData && !marketError && (
          <p className="mt-4 rounded-md border border-gray-200 bg-gray-50 p-4 text-sm text-gray-600">
            No market rows are stored for this symbol and date range.
          </p>
        )}

        {hasMarketData && (
          <div className="mt-4 h-80 w-full rounded-lg border border-gray-200 bg-white p-4" role="img" aria-label="NIFTY 50 closing price line chart">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={marketChartData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="date" tick={{ fontSize: 12 }} tickFormatter={(value: string) => formatDisplayDate(value)} />
                <YAxis tick={{ fontSize: 12 }} />
                <Tooltip labelFormatter={(value) => formatDisplayDate(String(value))} />
                <Legend />
                <Line type="monotone" dataKey="close" stroke="#2563eb" name="Close" dot={false} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        )}
      </section>

      <section className="rounded-lg border border-gray-200 bg-white p-5 shadow-sm">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <h3 className="text-lg font-semibold text-gray-900">Google Trends</h3>
            <p className="mt-1 text-sm text-gray-600">Relative search interest (0–100) for the selected configured term</p>
          </div>
          <div className="flex flex-col items-start gap-2 sm:items-end">
            <label htmlFor="search-term-select" className="text-sm font-medium text-gray-700">Search term</label>
            <select
              id="search-term-select"
              value={selectedTermId ?? ''}
              onChange={(event) => setSelectedTermId(event.target.value ? Number(event.target.value) : null)}
              disabled={!terms?.length}
              className="rounded-md border border-gray-300 px-3 py-2 text-sm"
              aria-describedby="search-term-help"
            >
              {!terms?.length && <option value="">No terms available</option>}
              {terms?.map((term: SearchTerm) => (
                <option key={term.id} value={term.id}>{term.term}</option>
              ))}
            </select>
            <p id="search-term-help" className="text-xs text-gray-500">
              {termsLoading ? 'Loading terms...' : termsError ? 'Term list unavailable' : `${terms?.length ?? 0} configured term(s)`}
            </p>
          </div>
        </div>

        {termsError && (
          <p role="alert" className="mt-4 rounded-md border border-red-200 bg-red-50 p-3 text-sm text-red-700">
            Failed to load search terms. {String(termsError)}
          </p>
        )}
        {!termsLoading && !termsError && !terms?.length && (
          <p className="mt-4 rounded-md border border-gray-200 bg-gray-50 p-4 text-sm text-gray-600">
            No search terms are configured. Add a term before requesting Trends data.
          </p>
        )}
        {trendsLoading && <p className="mt-4 text-sm text-gray-600">Loading Trends data...</p>}
        {trendsError && (
          <p role="alert" className="mt-4 rounded-md border border-red-200 bg-red-50 p-3 text-sm text-red-700">
            Failed to load Trends data. {String(trendsError)}
          </p>
        )}
        {trendsData !== undefined && !hasTrendsData && !trendsError && (
          <p className="mt-4 rounded-md border border-gray-200 bg-gray-50 p-4 text-sm text-gray-600">
            No Trends rows are stored for the selected term and date range.
          </p>
        )}

        {hasTrendsData && (
          <div className="mt-4 h-80 w-full rounded-lg border border-gray-200 bg-white p-4" role="img" aria-label="Google Trends search interest line chart">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={trendsChartData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="date" tick={{ fontSize: 12 }} tickFormatter={(value: string) => formatDisplayDate(value)} />
                <YAxis tick={{ fontSize: 12 }} domain={[0, 100]} />
                <Tooltip labelFormatter={(value) => formatDisplayDate(String(value))} />
                <Legend />
                <Line type="monotone" dataKey="interest_score" stroke="#16a34a" name="Interest" dot={false} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        )}
      </section>

      {!statusLoading && !statusError && marketData !== undefined && trendsData !== undefined && (
        <TrendInsights marketData={marketData} trendsData={trendsData} termName={activeTerm?.term} />
      )}

      <FeatureGlossary
        features={[...MARKET_FEATURES, ...trendFeatures(activeTerm?.term)]}
        title="Market and Trends feature guide"
        compact
      />
    </div>
  );
}
