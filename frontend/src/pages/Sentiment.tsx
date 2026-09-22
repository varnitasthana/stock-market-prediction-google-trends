import { useState } from 'react';
import { useMutation, useQuery } from '@tanstack/react-query';
import { analyzeSentimentText, fetchDailySentiment, fetchMarketDataStatus } from '../services/api';
import type { MarketDataStatusResponse, SentimentResponse, SentimentTextResponse } from '../types/api';
import HelpPanel from '../components/HelpPanel';
import PageIntro from '../components/PageIntro';
import StatusBadge from '../components/StatusBadge';
import { formatDisplayDate, getTodayISO } from '../utils/date';

const DEFAULT_SYMBOL = '^NSEI';

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

export default function Sentiment() {
  const [symbol, setSymbol] = useState(DEFAULT_SYMBOL);
  const [text, setText] = useState('');
  const [textResult, setTextResult] = useState<SentimentTextResponse | null>(null);

  const { data: marketStatus, isLoading: statusLoading, error: statusError } = useQuery({
    queryKey: ['marketStatus', DEFAULT_SYMBOL],
    queryFn: () => fetchMarketDataStatus(DEFAULT_SYMBOL),
  });

  const { data: dailySentiment, isLoading: dailyLoading, error: dailyError, isFetching } = useQuery({
    queryKey: ['dailySentiment', symbol.trim()],
    queryFn: () => fetchDailySentiment(symbol.trim()),
    enabled: symbol.trim().length > 0,
  });

  const textMutation = useMutation({
    mutationFn: () => analyzeSentimentText({ text: text.trim() }),
    onSuccess: (result) => setTextResult(result),
  });

  const sentimentDate = dailySentiment?.date ?? marketStatus?.last_stored_date ?? getTodayISO();
  const normalizedSymbol = symbol.trim();
  const canAnalyze = text.trim().length > 0 && !textMutation.isPending;

  return (
    <div className="space-y-6" aria-live="polite">
      <PageIntro
        title="Market Sentiment"
        description="Review stored market-derived sentiment and analyze the tone of financial text."
      >
        <StatusOverview status={marketStatus} loading={statusLoading} />
      </PageIntro>

      <HelpPanel title="How to read sentiment results">
        <p><strong>Purpose:</strong> Provide a simple positive, neutral, or negative view of stored market conditions and user-supplied text.</p>
        <p><strong>Inputs:</strong> A market symbol for daily sentiment and a short news headline, statement, or paragraph for text analysis.</p>
        <p><strong>Outputs:</strong> A sentiment score, label, source date, and counts of positive and negative terms for text.</p>
        <p><strong>Interpretation:</strong> Higher scores indicate more positive language or market-derived tone; lower scores indicate more negative tone. Treat the label as a summary, not a trading signal.</p>
        <p><strong>Limitations:</strong> Keyword-based text analysis can miss sarcasm, context, slang, and mixed statements. Daily sentiment reflects available stored data and may lag the Expected Session.</p>
        <p><strong>Historical patterns:</strong> Compare sentiment across several stored sessions and with market direction. Look for sustained shifts rather than reacting to one headline or one score.</p>
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

      <section className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <h3 className="text-lg font-semibold text-gray-900">Daily Market Sentiment</h3>
            <p className="mt-1 text-sm text-gray-600">Latest stored sentiment observation for the selected symbol.</p>
          </div>
          <StatusBadge label={`Sentiment Observation: ${formatDisplayDate(sentimentDate)}`} />
        </div>

        <div className="mt-5 max-w-md">
          <label htmlFor="sentiment-symbol" className="block text-sm font-medium text-gray-700">Market symbol</label>
          <input
            id="sentiment-symbol"
            value={symbol}
            onChange={(event) => setSymbol(event.target.value)}
            className="mt-1 w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
            aria-describedby="sentiment-symbol-help"
          />
          <p id="sentiment-symbol-help" className="mt-1 text-xs text-gray-500">Enter an NSE symbol, such as ^NSEI for NIFTY 50.</p>
        </div>

        {statusLoading && <p className="mt-4 text-sm text-gray-600">Checking stored market coverage...</p>}
        {dailyLoading && <p className="mt-4 text-sm text-gray-600">Loading daily sentiment...</p>}
        {dailyError && (
          <p role="alert" className="mt-4 rounded-md border border-red-200 bg-red-50 p-3 text-sm text-red-700">
            Failed to load daily sentiment. {String(dailyError)}
          </p>
        )}
        {!normalizedSymbol && !dailyLoading && !dailyError && (
          <p className="mt-4 rounded-md border border-gray-200 bg-gray-50 p-4 text-sm text-gray-600">Enter a market symbol to load its latest stored sentiment observation.</p>
        )}
        {dailySentiment && (
          <div className="mt-4 grid grid-cols-1 gap-4 sm:grid-cols-3">
            <Info label="Sentiment Score" value={dailySentiment.sentiment_score.toFixed(4)} />
            <Info label="Sentiment Label" value={dailySentiment.sentiment_label || 'N/A'} />
            <Info label="Source" value={dailySentiment.source || 'N/A'} />
            <Info label="Observation Date" value={formatDisplayDate(dailySentiment.date)} />
            <Info label="Latest Stored Session" value={formatDisplayDate(marketStatus?.last_stored_date)} />
            <Info label="Expected Session" value={formatDisplayDate(marketStatus?.expected_session)} />
          </div>
        )}
        {isFetching && <p className="mt-3 text-xs text-gray-500">Refreshing sentiment for the current symbol...</p>}
      </section>

      <section className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <h3 className="text-lg font-semibold text-gray-900">Text Sentiment Analysis</h3>
            <p className="mt-1 text-sm text-gray-600">Analyze the tone of financial news or another short text.</p>
          </div>
          <StatusBadge label={textResult ? 'Analysis available' : 'No analysis yet'} tone={textResult ? 'success' : 'neutral'} />
        </div>

        <div className="mt-5">
          <label htmlFor="sentiment-text" className="block text-sm font-medium text-gray-700">Text to analyze</label>
          <textarea
            id="sentiment-text"
            value={text}
            onChange={(event) => setText(event.target.value)}
            rows={5}
            maxLength={2000}
            className="mt-1 w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
            placeholder="Enter a news headline, market statement, or short paragraph..."
            aria-describedby="sentiment-text-help sentiment-text-count"
          />
          <div className="mt-1 flex items-center justify-between gap-3">
            <p id="sentiment-text-help" className="text-xs text-gray-500">Results are keyword-based and should be interpreted with the original context.</p>
            <p id="sentiment-text-count" className="text-xs text-gray-500">{text.length}/2000 characters</p>
          </div>
        </div>

        <div className="mt-4 flex flex-wrap items-center gap-3">
          <button
            type="button"
            onClick={() => textMutation.mutate()}
            disabled={!canAnalyze}
            className="rounded-md bg-blue-600 px-4 py-2 text-sm font-semibold text-white hover:bg-blue-500 disabled:cursor-not-allowed disabled:opacity-50"
            aria-describedby="analyze-text-help"
          >
            {textMutation.isPending ? 'Analyzing...' : 'Analyze Sentiment'}
          </button>
          <p id="analyze-text-help" className="text-xs text-gray-500">Enter at least one character before starting the analysis.</p>
        </div>

        {textMutation.isError && (
          <p role="alert" className="mt-4 rounded-md border border-red-200 bg-red-50 p-3 text-sm text-red-700">
            Text analysis failed. {String(textMutation.error)}
          </p>
        )}
        {textResult && (
          <div className="mt-5 grid grid-cols-1 gap-4 sm:grid-cols-3" role="status">
            <Info label="Score" value={textResult.score.toFixed(4)} />
            <Info label="Label" value={textResult.label || 'N/A'} />
            <Info label="Positive / Negative Terms" value={`${textResult.positive_count} / ${textResult.negative_count}`} />
          </div>
        )}
      </section>
    </div>
  );
}

function Info({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <p className="text-xs text-gray-500">{label}</p>
      <p className="mt-1 text-sm font-medium text-gray-900">{value}</p>
    </div>
  );
}
