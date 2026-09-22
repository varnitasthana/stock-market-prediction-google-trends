import { useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';
import { analyzeStatistics, fetchMarketDataStatus } from '../services/api';
import type { MarketDataStatusResponse } from '../types/api';
import FeatureGlossary from '../components/FeatureGlossary';
import HelpPanel from '../components/HelpPanel';
import PageIntro from '../components/PageIntro';
import StatusBadge from '../components/StatusBadge';
import { formatDisplayDate, formatDisplayDateRange, getTodayISO } from '../utils/date';

const DEFAULT_SYMBOL = '^NSEI';
const SAFE_START = '2024-01-01';

function StatusOverview({ status, loading }: { status?: MarketDataStatusResponse | null; loading: boolean }) {
  if (loading) {
    return <StatusBadge label="Checking market status" />;
  }

  if (!status) {
    return <StatusBadge label="Using safe date defaults" tone="warning" />;
  }

  return (
    <div className="flex flex-wrap gap-2">
      <StatusBadge label={`Today: ${formatDisplayDate(status.today)}`} />
      <StatusBadge label={`Expected Session: ${formatDisplayDate(status.expected_session)}`} tone={status.is_stale ? 'warning' : 'success'} />
      <StatusBadge label={`Latest Stored Session: ${formatDisplayDate(status.last_stored_date)}`} tone={status.is_stale ? 'warning' : 'success'} />
    </div>
  );
}

export default function Statistics() {
  const { data: marketStatus, isLoading: statusLoading, error: statusError } = useQuery({
    queryKey: ['marketStatus', DEFAULT_SYMBOL],
    queryFn: () => fetchMarketDataStatus(DEFAULT_SYMBOL),
  });

  const rangeStart = marketStatus?.first_stored_date ?? SAFE_START;
  const rangeEnd = marketStatus?.last_stored_date ?? marketStatus?.expected_session ?? getTodayISO();

  const { data, isLoading, error } = useQuery({
    queryKey: ['statistics', DEFAULT_SYMBOL, rangeStart, rangeEnd],
    queryFn: () => analyzeStatistics({ symbol: DEFAULT_SYMBOL, start_date: rangeStart, end_date: rangeEnd }),
    enabled: !!marketStatus || !!statusError,
  });

  const featureNames = useMemo(() => {
    if (!data) return [];

    return Array.from(new Set([
      ...data.descriptive_statistics.map((row) => row.feature),
      ...data.correlations.map((row) => row.feature),
      ...data.lag_analysis.map((row) => row.feature),
      ...Object.values(data.direction_analysis).flatMap((rows) => rows.map((row) => row.feature)),
    ]));
  }, [data]);

  const sampleRange = data?.date_range ? formatDisplayDateRange(data.date_range) : `${formatDisplayDate(rangeStart)} to ${formatDisplayDate(rangeEnd)}`;

  return (
    <div className="space-y-6" aria-live="polite">
      <PageIntro
        title="Statistical Analysis"
        description="Review historical associations between engineered features and the next-session targets."
      >
        <StatusOverview status={marketStatus} loading={statusLoading} />
      </PageIntro>

      <HelpPanel title="How to read this analysis">
        <p><strong>Purpose:</strong> Summarize the stored sample and show correlations, lag relationships, and direction-group differences.</p>
        <p><strong>Inputs:</strong> Market and Trends features from the Latest Stored Session window. Today and Expected Session are freshness references, not guaranteed data rows.</p>
        <p><strong>Outputs:</strong> Descriptive statistics, correlation tests, lag analysis, and comparisons by market direction.</p>
        <p><strong>Interpretation:</strong> A correlation near 0 suggests little linear association in this sample; a larger absolute value deserves further checking. Positive and negative SHAP-style patterns are not shown here, so use the Explainability page for a specific prediction.</p>
        <p><strong>Limitations:</strong> Correlation does not imply causation. Google Trends is a relative 0–100 measure, and a small or stale sample can produce unstable results.</p>
        <p><strong>Historical patterns:</strong> Compare several lags and direction groups, then check whether a relationship repeats across time instead of relying on one significant row.</p>
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

      {isLoading && <p className="rounded-lg border border-gray-200 bg-white p-5 text-sm text-gray-600">Loading statistical analysis...</p>}
      {error && (
        <p role="alert" className="rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-700">
          Failed to load statistics. {String(error)}
        </p>
      )}
      {!isLoading && !error && !data && (
        <p className="rounded-lg border border-gray-200 bg-white p-5 text-sm text-gray-600">No statistics are available for the selected stored window.</p>
      )}

      {data && (
        <>
          <section className="rounded-lg border border-gray-200 bg-white p-5 shadow-sm">
            <div className="flex flex-wrap items-start justify-between gap-3">
              <div>
                <h3 className="text-lg font-semibold text-gray-900">Dataset Info</h3>
                <p className="mt-1 text-sm text-gray-600">The analysis window is based on stored data, not a hard-coded end date.</p>
              </div>
              <StatusBadge label={`Sample: ${data.sample_size} row(s)`} />
            </div>
            <div className="mt-4 grid grid-cols-1 gap-4 sm:grid-cols-3">
              <InfoCard title="Symbol" value={data.symbol} />
              <InfoCard title="Analyzed Date Range" value={sampleRange} />
              <InfoCard title="Sample Size" value={String(data.sample_size)} />
            </div>
          </section>

          <FeatureGlossary features={featureNames} title="Features in this analysis" compact />

          <section className="rounded-lg border border-gray-200 bg-white p-5 shadow-sm">
            <h3 className="text-lg font-semibold text-gray-900">Descriptive Statistics</h3>
            <p className="mt-1 text-sm text-gray-600">These values describe the selected historical sample.</p>
            {data.descriptive_statistics.length === 0 ? (
              <p className="mt-4 rounded-md border border-gray-200 bg-gray-50 p-4 text-sm text-gray-600">No descriptive statistics are available.</p>
            ) : (
              <div className="mt-4 overflow-x-auto rounded-lg border border-gray-200 bg-white">
                <table className="min-w-full divide-y divide-gray-200" aria-label="Descriptive statistics by feature">
                  <thead className="bg-gray-50">
                    <tr>
                      <th scope="col" className="px-4 py-2 text-left text-xs font-medium text-gray-500">Feature</th>
                      <th scope="col" className="px-4 py-2 text-right text-xs font-medium text-gray-500">Mean</th>
                      <th scope="col" className="px-4 py-2 text-right text-xs font-medium text-gray-500">Median</th>
                      <th scope="col" className="px-4 py-2 text-right text-xs font-medium text-gray-500">Std</th>
                      <th scope="col" className="px-4 py-2 text-right text-xs font-medium text-gray-500">Min</th>
                      <th scope="col" className="px-4 py-2 text-right text-xs font-medium text-gray-500">Max</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-100">
                    {data.descriptive_statistics.map((row) => (
                      <tr key={row.feature}>
                        <td className="px-4 py-2 text-sm text-gray-900">{row.feature}</td>
                        <td className="px-4 py-2 text-right text-sm text-gray-700">{row.mean.toFixed(4)}</td>
                        <td className="px-4 py-2 text-right text-sm text-gray-700">{row.median.toFixed(4)}</td>
                        <td className="px-4 py-2 text-right text-sm text-gray-700">{row.std.toFixed(4)}</td>
                        <td className="px-4 py-2 text-right text-sm text-gray-700">{row.min.toFixed(4)}</td>
                        <td className="px-4 py-2 text-right text-sm text-gray-700">{row.max.toFixed(4)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </section>

          <section className="rounded-lg border border-gray-200 bg-white p-5 shadow-sm">
            <h3 className="text-lg font-semibold text-gray-900">Correlations</h3>
            <p className="mt-1 text-sm text-gray-600">Linear association between each feature and target in the stored sample.</p>
            {data.correlations.length === 0 ? (
              <p className="mt-4 rounded-md border border-gray-200 bg-gray-50 p-4 text-sm text-gray-600">No correlation results are available.</p>
            ) : (
              <div className="mt-4 overflow-x-auto rounded-lg border border-gray-200 bg-white">
                <table className="min-w-full divide-y divide-gray-200" aria-label="Feature correlations with targets">
                  <thead className="bg-gray-50">
                    <tr>
                      <th scope="col" className="px-4 py-2 text-left text-xs font-medium text-gray-500">Feature</th>
                      <th scope="col" className="px-4 py-2 text-left text-xs font-medium text-gray-500">Target</th>
                      <th scope="col" className="px-4 py-2 text-right text-xs font-medium text-gray-500">Correlation</th>
                      <th scope="col" className="px-4 py-2 text-right text-xs font-medium text-gray-500">p-value</th>
                      <th scope="col" className="px-4 py-2 text-right text-xs font-medium text-gray-500">Adjusted p-value</th>
                      <th scope="col" className="px-4 py-2 text-center text-xs font-medium text-gray-500">Significant (0.05)</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-100">
                    {data.correlations.map((row) => (
                      <tr key={`${row.feature}-${row.target}`}>
                        <td className="px-4 py-2 text-sm text-gray-900">{row.feature}</td>
                        <td className="px-4 py-2 text-sm text-gray-700">{row.target}</td>
                        <td className="px-4 py-2 text-right text-sm text-gray-700">{row.correlation.toFixed(4)}</td>
                        <td className="px-4 py-2 text-right text-sm text-gray-700">{row.p_value.toFixed(4)}</td>
                        <td className="px-4 py-2 text-right text-sm text-gray-700">{row.adjusted_p_value?.toFixed(4) ?? 'N/A'}</td>
                        <td className="px-4 py-2 text-center text-sm">{row.significant_at_0_05 === null ? 'N/A' : row.significant_at_0_05 ? 'Yes' : 'No'}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </section>

          <section className="rounded-lg border border-gray-200 bg-white p-5 shadow-sm">
            <h3 className="text-lg font-semibold text-gray-900">Lag Analysis</h3>
            <p className="mt-1 text-sm text-gray-600">Check whether earlier feature values have a historical relationship with the target.</p>
            {data.lag_analysis.length === 0 ? (
              <p className="mt-4 rounded-md border border-gray-200 bg-gray-50 p-4 text-sm text-gray-600">No lag results are available.</p>
            ) : (
              <div className="mt-4 overflow-x-auto rounded-lg border border-gray-200 bg-white">
                <table className="min-w-full divide-y divide-gray-200" aria-label="Lag analysis">
                  <thead className="bg-gray-50">
                    <tr>
                      <th scope="col" className="px-4 py-2 text-left text-xs font-medium text-gray-500">Feature</th>
                      <th scope="col" className="px-4 py-2 text-left text-xs font-medium text-gray-500">Target</th>
                      <th scope="col" className="px-4 py-2 text-right text-xs font-medium text-gray-500">Correlation</th>
                      <th scope="col" className="px-4 py-2 text-right text-xs font-medium text-gray-500">p-value</th>
                      <th scope="col" className="px-4 py-2 text-right text-xs font-medium text-gray-500">Sample Size</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-100">
                    {data.lag_analysis.map((row) => (
                      <tr key={`${row.feature}-${row.target}`}>
                        <td className="px-4 py-2 text-sm text-gray-900">{row.feature}</td>
                        <td className="px-4 py-2 text-sm text-gray-700">{row.target}</td>
                        <td className="px-4 py-2 text-right text-sm text-gray-700">{row.correlation.toFixed(4)}</td>
                        <td className="px-4 py-2 text-right text-sm text-gray-700">{row.p_value.toFixed(4)}</td>
                        <td className="px-4 py-2 text-right text-sm text-gray-700">{row.sample_size}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </section>

          <section className="rounded-lg border border-gray-200 bg-white p-5 shadow-sm">
            <h3 className="text-lg font-semibold text-gray-900">Direction Groups</h3>
            <p className="mt-1 text-sm text-gray-600">Compare feature values when the target direction was positive or negative.</p>
            {Object.keys(data.direction_analysis).length === 0 ? (
              <p className="mt-4 rounded-md border border-gray-200 bg-gray-50 p-4 text-sm text-gray-600">No direction-group results are available.</p>
            ) : (
              <div className="mt-4 space-y-4">
                {Object.entries(data.direction_analysis).map(([direction, rows]) => (
                  <div key={direction} className="rounded-md border border-gray-100 bg-gray-50 p-4">
                    <h4 className="text-sm font-semibold text-gray-900">{direction.split('_').join(' ')}</h4>
                    {rows.length === 0 ? (
                      <p className="mt-2 text-sm text-gray-600">No feature rows for this direction.</p>
                    ) : (
                      <div className="mt-3 overflow-x-auto">
                        <table className="min-w-full divide-y divide-gray-200" aria-label={`Direction group ${direction}`}>
                          <thead className="bg-white">
                            <tr>
                              <th scope="col" className="px-3 py-2 text-left text-xs font-medium text-gray-500">Feature</th>
                              <th scope="col" className="px-3 py-2 text-right text-xs font-medium text-gray-500">Mean</th>
                              <th scope="col" className="px-3 py-2 text-right text-xs font-medium text-gray-500">Median</th>
                              <th scope="col" className="px-3 py-2 text-right text-xs font-medium text-gray-500">Std</th>
                              <th scope="col" className="px-3 py-2 text-right text-xs font-medium text-gray-500">Count</th>
                            </tr>
                          </thead>
                          <tbody className="divide-y divide-gray-100">
                            {rows.map((row) => (
                              <tr key={`${direction}-${row.feature}`}>
                                <td className="px-3 py-2 text-sm text-gray-900">{row.feature}</td>
                                <td className="px-3 py-2 text-right text-sm text-gray-700">{row.mean.toFixed(4)}</td>
                                <td className="px-3 py-2 text-right text-sm text-gray-700">{row.median.toFixed(4)}</td>
                                <td className="px-3 py-2 text-right text-sm text-gray-700">{row.std.toFixed(4)}</td>
                                <td className="px-3 py-2 text-right text-sm text-gray-700">{row.count}</td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </section>
        </>
      )}
    </div>
  );
}

function InfoCard({ title, value }: { title: string; value: string }) {
  return (
    <div className="rounded-lg border border-gray-200 bg-white p-5 shadow-sm">
      <p className="text-sm font-medium text-gray-500">{title}</p>
      <p className="mt-2 text-xl font-semibold text-gray-900">{value}</p>
    </div>
  );
}
