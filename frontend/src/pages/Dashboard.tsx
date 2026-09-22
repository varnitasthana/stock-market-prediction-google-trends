import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import HelpPanel from '../components/HelpPanel';
import PageIntro from '../components/PageIntro';
import StatusBadge from '../components/StatusBadge';
import { fetchDashboardSummary, fetchMarketDataStatus, fetchModelRuns, fetchSearchTerms, refreshMarketData } from '../services/api';
import type { DashboardSummary, MarketDataStatusResponse, ModelRun, SearchTerm } from '../types/api';
import { formatDisplayDate } from '../utils/date';

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
  const queryClient = useQueryClient();

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

  const refreshMutation = useMutation({
    mutationFn: () => refreshMarketData({ symbol, lookback_days: 30 }),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['marketStatus', symbol] });
      void queryClient.invalidateQueries({ queryKey: ['dashboard', symbol] });
    },
  });

  const modelCount = models?.length ?? 0;
  const classificationModels = models?.filter((m: ModelRun) => m.task_type === 'classification').length ?? 0;
  const regressionModels = models?.filter((m: ModelRun) => m.task_type === 'regression').length ?? 0;

  const today = marketStatus?.today ?? 'N/A';
  const expectedSession = marketStatus?.expected_session ?? 'N/A';
  const lastStoredDate = marketStatus?.last_stored_date ?? summary?.latest_date ?? 'N/A';
  const isDataStale = marketStatus?.is_stale ?? false;
  const sessionsBehind = marketStatus?.sessions_behind ?? 0;
  const refreshing = refreshMutation.isPending;
  const refreshMessage = refreshMutation.data?.message;

  return (
    <div className="space-y-6">
      <PageIntro
        title="Understand the market before using a prediction"
        description="Start with data freshness, then inspect historical patterns, statistics, models, and finally predictions."
      >
        <StatusBadge label={isDataStale ? 'Data needs refresh' : 'Data current'} tone={isDataStale ? 'warning' : 'success'} />
      </PageIntro>

      <section className="rounded-lg border border-gray-200 bg-white p-5 shadow-sm">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <h2 className="text-xl font-semibold text-gray-900">Date and freshness</h2>
            <p className="mt-1 text-sm text-gray-600">Today is the calendar date. Expected session is the latest session that should be available. Latest stored session is the last row actually in the database.</p>
          </div>
          <button
            onClick={() => refreshMutation.mutate()}
            disabled={refreshing}
            className="rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-60"
          >
            {refreshing ? 'Refreshing...' : 'Refresh market data'}
          </button>
        </div>
        <div className="mt-4 grid grid-cols-1 gap-3 sm:grid-cols-3">
          <DateCard label="Today" value={formatDisplayDate(today)} />
          <DateCard label="Expected session" value={formatDisplayDate(expectedSession)} />
          <DateCard label="Latest stored session" value={formatDisplayDate(lastStoredDate)} tone={isDataStale ? 'warning' : 'success'} />
        </div>
        {isDataStale && (
          <p className="mt-3 text-sm text-yellow-800">
            Data is {sessionsBehind} session(s) behind. Refreshing downloads the recent window and recomputes derived metrics; it does not invent missing values.
          </p>
        )}
        {refreshMessage && <p className="mt-3 text-sm text-gray-700">{refreshMessage}</p>}
      </section>

      <section>
        <h2 className="text-xl font-semibold text-gray-900">Pipeline Overview</h2>
        <p className="mt-1 text-sm text-gray-500">Each stage transforms raw observations into information the model can use.</p>
        <div className="mt-4 flex flex-wrap items-center gap-2">
          {PIPELINE_STEPS.map((step, index) => (
            <span key={step} className="flex items-center gap-2">
              <span className="rounded-full bg-blue-50 px-3 py-1 text-xs font-medium text-blue-700">{step}</span>
              {index < PIPELINE_STEPS.length - 1 && <span className="text-gray-400">→</span>}
            </span>
          ))}
        </div>
      </section>

      <section>
        <h2 className="text-xl font-semibold text-gray-900">Project Summary</h2>
        <div className="mt-4 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <SummaryCard title="Symbol" value={summary?.symbol ?? symbol} loading={summaryLoading} />
          <SummaryCard title="Latest Close" value={summary?.latest_close != null ? Number(summary.latest_close).toFixed(2) : 'N/A'} loading={summaryLoading} />
          <SummaryCard title="Daily Return" value={summary?.latest_daily_return != null ? Number(summary.latest_daily_return).toFixed(4) : 'N/A'} loading={summaryLoading} />
          <SummaryCard title="Models Trained" value={String(modelCount)} loading={summaryLoading} />
          <SummaryCard title="Classification Models" value={String(classificationModels)} loading={summaryLoading} />
          <SummaryCard title="Regression Models" value={String(regressionModels)} loading={summaryLoading} />
          <SummaryCard title="Search Terms" value={String(terms?.length ?? 0)} loading={summaryLoading} />
          <SummaryCard title="Stored Rows" value={String(marketStatus?.row_count ?? 'N/A')} loading={summaryLoading} />
        </div>
      </section>

      <HelpPanel title="How to use this dashboard" defaultOpen>
        <p><span className="font-semibold">1. Check freshness:</span> use the three date cards above. A stale badge means the latest stored session is older than expected.</p>
        <p><span className="font-semibold">2. Inspect history:</span> open Data Explorer to compare price movement with Google Trends interest.</p>
        <p><span className="font-semibold">3. Study relationships:</span> use Statistics to review correlation, lag, and direction-group results.</p>
        <p><span className="font-semibold">4. Review the model:</span> use Models and Explainability to understand what was trained and which inputs influenced a result.</p>
        <p><span className="font-semibold">5. Treat predictions as estimates:</span> they are historical-pattern estimates, not investment advice or guarantees.</p>
      </HelpPanel>

      {summaryError && (
        <p className="text-sm text-red-600">Failed to load dashboard summary: {String(summaryError)}</p>
      )}
    </div>
  );
}

function DateCard({ label, value, tone }: { label: string; value: string; tone?: 'success' | 'warning' }) {
  return (
    <div className="rounded-md border border-gray-100 bg-gray-50 p-4">
      <p className="text-xs font-medium text-gray-500">{label}</p>
      <p className={`mt-2 text-lg font-semibold ${tone === 'warning' ? 'text-yellow-800' : 'text-gray-900'}`}>{value}</p>
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
