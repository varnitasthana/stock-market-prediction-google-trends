import { useQuery } from '@tanstack/react-query';
import { fetchDashboardSummary, fetchSearchTerms, fetchModelRuns, fetchMarketDataStatus } from '../services/api';
import type { DashboardSummary, SearchTerm, ModelRun, MarketDataStatusResponse } from '../types/api';

const PIPELINE_STEPS = [
  'Google Trends',
  'Market Data',
  'Cleaning',
  'Feature Engineering',
  'Statistics',
  'ML Dataset',
  'Training',
  'Evaluation',
  'Prediction',
];

export default function Dashboard({ symbol }: { symbol: string }) {
  const { data: summary, isLoading: summaryLoading, error: summaryError } = useQuery({
    queryKey: ['dashboard', symbol],
    queryFn: () => fetchDashboardSummary(symbol),
  });

  const { data: terms } = useQuery({
    queryKey: ['searchTerms'],
    queryFn: fetchSearchTerms,
  });

  const { data: models } = useQuery({
    queryKey: ['modelRuns'],
    queryFn: () => fetchModelRuns(),
  });

  const { data: marketStatus } = useQuery({
    queryKey: ['marketStatus', symbol],
    queryFn: () => fetchMarketDataStatus(symbol),
  });

  const modelCount = models?.length ?? 0;
  const classificationModels = models?.filter((m: ModelRun) => m.task_type === 'classification').length ?? 0;
  const regressionModels = models?.filter((m: ModelRun) => m.task_type === 'regression').length ?? 0;

  const today = new Date().toISOString().split('T')[0];
  const isDataStale = marketStatus?.is_stale ?? false;
  const sessionsBehind = marketStatus?.sessions_behind ?? 0;
  const lastStoredDate = marketStatus?.last_stored_date ?? summary?.latest_date ?? 'N/A';

  return (
    <div className="space-y-6">
      <section>
        <h2 className="text-xl font-semibold text-gray-900">Pipeline Overview</h2>
        <p className="mt-1 text-sm text-gray-500">End-to-end ML pipeline from data ingestion to prediction</p>
        <div className="mt-4 flex flex-wrap items-center gap-2">
          {PIPELINE_STEPS.map((step, index) => (
            <span key={step} className="flex items-center gap-2">
              <span className="rounded-full bg-blue-50 px-3 py-1 text-xs font-medium text-blue-700">{step}</span>
              {index < PIPELINE_STEPS.length - 1 && <span className="text-gray-400">↓</span>}
            </span>
          ))}
        </div>
      </section>

      <section>
        <h2 className="text-xl font-semibold text-gray-900">Project Summary</h2>
        <div className="mt-4 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <SummaryCard title="Symbol" value={summary?.symbol ?? symbol} loading={summaryLoading} />
          <SummaryCard title="Latest Close" value={summary?.latest_close != null ? Number(summary.latest_close).toFixed(2) : 'N/A'} loading={summaryLoading} />
          <SummaryCard 
            title="Latest Data Date" 
            value={lastStoredDate} 
            loading={summaryLoading}
            subtitle={isDataStale ? `Data is ${sessionsBehind} session(s) behind (today: ${today})` : 'Data is current'}
          />
          <SummaryCard title="Daily Return" value={summary?.latest_daily_return != null ? Number(summary.latest_daily_return).toFixed(4) : 'N/A'} loading={summaryLoading} />
          <SummaryCard title="Models Trained" value={String(modelCount)} loading={summaryLoading} />
          <SummaryCard title="Classification Models" value={String(classificationModels)} loading={summaryLoading} />
          <SummaryCard title="Regression Models" value={String(regressionModels)} loading={summaryLoading} />
          <SummaryCard title="Search Terms" value={String(terms?.length ?? 0)} loading={summaryLoading} />
        </div>
      </section>

      {isDataStale && (
        <section className="rounded-lg border border-yellow-200 bg-yellow-50 p-4 text-sm text-yellow-800">
          <p className="font-medium">Data Freshness Notice</p>
          <p className="mt-1">{marketStatus?.message}</p>
          <p className="mt-1">The model predictions are based on data up to {lastStoredDate}. Consider refreshing market data for the latest sessions.</p>
        </section>
      )}

      <section className="rounded-lg border border-yellow-200 bg-yellow-50 p-4 text-sm text-yellow-800">
        <p className="font-medium">Dataset limitation</p>
        <p className="mt-1">The current dataset contains 114 observations from 2024-01-01 to 2024-06-30. The final test set contains 18 observations. Metrics are sample-specific and should not be interpreted as guaranteed future performance.</p>
      </section>

      {summaryError && (
        <p className="text-sm text-red-600">Failed to load dashboard summary: {String(summaryError)}</p>
      )}
    </div>
  );
}

function SummaryCard({ title, value, loading, subtitle }: { title: string; value: string; loading: boolean; subtitle?: string }) {
  return (
    <div className="rounded-lg border border-gray-200 bg-white p-5 shadow-sm">
      <p className="text-sm font-medium text-gray-500">{title}</p>
      <p className="mt-2 text-2xl font-semibold text-gray-900">{loading ? '...' : value}</p>
      {subtitle && <p className="mt-1 text-xs text-gray-500">{subtitle}</p>}
    </div>
  );
}
