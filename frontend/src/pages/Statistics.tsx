import { useQuery } from '@tanstack/react-query';
import { analyzeStatistics } from '../services/api';
import type { StatisticsAnalyzeResponse } from '../types/api';

const DEFAULT_SYMBOL = '^NSEI';
const DEFAULT_START = '2024-01-01';
const DEFAULT_END = '2026-09-21';

export default function Statistics() {
  const { data, isLoading, error } = useQuery({
    queryKey: ['statistics', DEFAULT_SYMBOL, DEFAULT_START, DEFAULT_END],
    queryFn: () => analyzeStatistics({ symbol: DEFAULT_SYMBOL, start_date: DEFAULT_START, end_date: DEFAULT_END }),
  });

  if (isLoading) return <p className="text-gray-600">Loading statistical analysis...</p>;
  if (error) return <p className="text-red-600">Failed to load statistics.</p>;
  if (!data) return <p className="text-gray-600">No statistics available.</p>;

  return (
    <div className="space-y-6">
      <section>
        <h2 className="text-xl font-semibold text-gray-900">Statistical Analysis</h2>
        <p className="mt-1 text-sm text-gray-500">Historical associations between features and targets in the sample</p>
        <div className="mt-4 rounded-lg border border-yellow-200 bg-yellow-50 p-4 text-sm text-yellow-800">
          Correlation does not imply causation. Google Trends measures relative search interest on a 0–100 scale. These results describe associations in a small historical sample, not guaranteed future market behavior.
        </div>
      </section>

      <section>
        <h3 className="text-lg font-medium text-gray-900">Dataset Info</h3>
        <div className="mt-2 grid grid-cols-1 gap-4 sm:grid-cols-3">
          <InfoCard title="Symbol" value={data.symbol} />
          <InfoCard title="Date Range" value={data.date_range} />
          <InfoCard title="Sample Size" value={String(data.sample_size)} />
        </div>
      </section>

      <section>
        <h3 className="text-lg font-medium text-gray-900">Descriptive Statistics</h3>
        <div className="mt-2 overflow-x-auto rounded-lg border border-gray-200 bg-white">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-4 py-2 text-left text-xs font-medium text-gray-500">Feature</th>
                <th className="px-4 py-2 text-right text-xs font-medium text-gray-500">Mean</th>
                <th className="px-4 py-2 text-right text-xs font-medium text-gray-500">Median</th>
                <th className="px-4 py-2 text-right text-xs font-medium text-gray-500">Std</th>
                <th className="px-4 py-2 text-right text-xs font-medium text-gray-500">Min</th>
                <th className="px-4 py-2 text-right text-xs font-medium text-gray-500">Max</th>
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
      </section>

      <section>
        <h3 className="text-lg font-medium text-gray-900">Correlations</h3>
        <div className="mt-2 overflow-x-auto rounded-lg border border-gray-200 bg-white">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-4 py-2 text-left text-xs font-medium text-gray-500">Feature</th>
                <th className="px-4 py-2 text-left text-xs font-medium text-gray-500">Target</th>
                <th className="px-4 py-2 text-right text-xs font-medium text-gray-500">Correlation</th>
                <th className="px-4 py-2 text-right text-xs font-medium text-gray-500">p-value</th>
                <th className="px-4 py-2 text-right text-xs font-medium text-gray-500">Adjusted p-value</th>
                <th className="px-4 py-2 text-center text-xs font-medium text-gray-500">Significant (0.05)</th>
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
                  <td className="px-4 py-2 text-center text-sm">{row.significant_at_0_05 ? 'Yes' : 'No'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
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
