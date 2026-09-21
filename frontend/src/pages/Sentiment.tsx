import { useQuery } from '@tanstack/react-query';
import { fetchDailySentiment, analyzeSentimentText } from '../services/api';
import type { SentimentResponse, SentimentTextResponse } from '../types/api';
import { useState } from 'react';

const DEFAULT_SYMBOL = '^NSEI';

export default function Sentiment() {
  const [symbol, setSymbol] = useState(DEFAULT_SYMBOL);
  const [text, setText] = useState('');
  const [textResult, setTextResult] = useState<SentimentTextResponse | null>(null);

  const { data: dailySentiment, isLoading: dailyLoading, error: dailyError } = useQuery({
    queryKey: ['dailySentiment', symbol],
    queryFn: () => fetchDailySentiment(symbol),
  });

  const handleAnalyzeText = async () => {
    if (!text.trim()) return;
    const result = await analyzeSentimentText({ text: text.trim() });
    setTextResult(result);
  };

  return (
    <div className="space-y-6">
      <section>
        <h2 className="text-xl font-semibold text-gray-900">Market Sentiment</h2>
        <p className="mt-1 text-sm text-gray-500">Daily sentiment derived from market data and text analysis</p>
      </section>

      <section className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm">
        <h3 className="text-lg font-medium text-gray-900">Daily Sentiment</h3>
        <div className="mt-4 grid grid-cols-1 gap-4 sm:grid-cols-3">
          <div>
            <label className="block text-sm font-medium text-gray-700">Symbol</label>
            <input value={symbol} onChange={(e) => setSymbol(e.target.value)} className="mt-1 rounded-md border border-gray-300 px-3 py-2 text-sm" />
          </div>
        </div>
        {dailyLoading && <p className="mt-2 text-sm text-gray-600">Loading sentiment...</p>}
        {dailyError && <p className="mt-2 text-sm text-red-600">Failed to load sentiment.</p>}
        {!dailyLoading && !dailyError && dailySentiment && (
          <div className="mt-4 grid grid-cols-1 gap-4 sm:grid-cols-3">
            <Info label="Sentiment Score" value={dailySentiment.sentiment_score.toFixed(4)} />
            <Info label="Sentiment Label" value={dailySentiment.sentiment_label} />
            <Info label="Source" value={dailySentiment.source} />
          </div>
        )}
      </section>

      <section className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm">
        <h3 className="text-lg font-medium text-gray-900">Text Sentiment Analysis</h3>
        <p className="mt-1 text-sm text-gray-500">Analyze the sentiment of financial news or any text</p>
        <textarea
          value={text}
          onChange={(e) => setText(e.target.value)}
          rows={4}
          className="mt-4 w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
          placeholder="Enter text to analyze..."
        />
        <div className="mt-4">
          <button onClick={handleAnalyzeText} disabled={!text.trim()} className="rounded-md bg-blue-600 px-4 py-2 text-sm font-semibold text-white hover:bg-blue-500 disabled:opacity-50">
            Analyze Sentiment
          </button>
        </div>
        {textResult && (
          <div className="mt-4 grid grid-cols-1 gap-4 sm:grid-cols-3">
            <Info label="Score" value={textResult.score.toFixed(4)} />
            <Info label="Label" value={textResult.label} />
            <Info label="Positive / Negative" value={`${textResult.positive_count} / ${textResult.negative_count}`} />
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
      <p className="text-sm font-medium text-gray-900">{value}</p>
    </div>
  );
}
