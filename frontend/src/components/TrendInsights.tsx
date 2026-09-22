import { MarketDataPoint, TrendDataPoint } from '../types/api';

interface TrendInsightsProps {
  marketData: MarketDataPoint[];
  trendsData: TrendDataPoint[];
  termName?: string;
}

function sortedMarketData(data: MarketDataPoint[]): MarketDataPoint[] {
  return [...data].sort((a, b) => a.date.localeCompare(b.date));
}

function sortedTrendData(data: TrendDataPoint[]): TrendDataPoint[] {
  return [...data].sort((a, b) => a.date.localeCompare(b.date));
}

function percent(value: number): string {
  return `${(value * 100).toFixed(2)}%`;
}

export default function TrendInsights({ marketData, trendsData, termName }: TrendInsightsProps) {
  const market = sortedMarketData(marketData);
  const trends = sortedTrendData(trendsData);
  const firstClose = market.length ? Number(market[0].close) : null;
  const lastClose = market.length ? Number(market[market.length - 1].close) : null;
  const periodReturn = firstClose && lastClose ? (lastClose - firstClose) / firstClose : null;
  const positiveSessions = market.filter((row) => Number(row.daily_return) > 0).length;
  const negativeSessions = market.filter((row) => Number(row.daily_return) < 0).length;
  const firstInterest = trends.length ? Number(trends[0].interest_score) : null;
  const lastInterest = trends.length ? Number(trends[trends.length - 1].interest_score) : null;
  const interestChange = firstInterest !== null && lastInterest !== null ? lastInterest - firstInterest : null;
  const latestMarketDate = market.length ? market[market.length - 1].date : 'N/A';
  const latestTrendDate = trends.length ? trends[trends.length - 1].date : 'N/A';

  const direction = periodReturn === null ? 'insufficient data' : periodReturn > 0 ? 'upward' : periodReturn < 0 ? 'downward' : 'flat';
  const termLabel = termName || 'the selected search term';

  return (
    <section className="rounded-lg border border-gray-200 bg-white p-5 shadow-sm space-y-4">
      <div>
        <h3 className="text-lg font-semibold text-gray-900">Historical Pattern Summary</h3>
        <p className="mt-1 text-sm text-gray-600">A plain-language snapshot of the selected historical window.</p>
      </div>

      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <Insight label="Market period return" value={periodReturn === null ? 'N/A' : percent(periodReturn)} />
        <Insight label="Observed direction" value={direction} />
        <Insight label="Positive / negative sessions" value={`${positiveSessions} / ${negativeSessions}`} />
        <Insight label={`${termLabel} interest change`} value={interestChange === null ? 'N/A' : `${interestChange >= 0 ? '+' : ''}${interestChange.toFixed(1)} pts`} />
      </div>

      <div className="rounded-md bg-blue-50 p-4 text-sm text-blue-900">
        <p className="font-semibold">How to analyze this pattern</p>
        <ul className="mt-2 list-disc space-y-1 pl-5">
          <li>Compare the market direction with changes in search interest, but treat the relationship as a clue rather than proof.</li>
          <li>Look for repeated patterns across several sessions, not a single large candle or one unusual search spike.</li>
          <li>Use volatility and the number of positive versus negative sessions to judge whether the move was steady or unstable.</li>
          <li>Check the Statistics page for correlation, lag, and direction-group results before drawing a conclusion.</li>
        </ul>
      </div>

      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
        <p className="text-sm text-gray-600"><span className="font-semibold text-gray-800">Market data through: </span>{latestMarketDate}</p>
        <p className="text-sm text-gray-600"><span className="font-semibold text-gray-800">Trends data through: </span>{latestTrendDate}</p>
      </div>
    </section>
  );
}

function Insight({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-md border border-gray-100 bg-gray-50 p-4">
      <p className="text-xs font-medium text-gray-500">{label}</p>
      <p className="mt-2 text-lg font-semibold text-gray-900">{value}</p>
    </div>
  );
}
