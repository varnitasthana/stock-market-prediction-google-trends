import { useMemo, useState } from 'react';

export interface FeatureDefinition {
  name: string;
  label: string;
  description: string;
  howToRead: string;
}

const FEATURE_DEFINITIONS: FeatureDefinition[] = [
  {
    name: 'daily_return',
    label: 'Daily return',
    description: 'Percentage change in the closing price from the previous trading session.',
    howToRead: 'Positive means the index rose; negative means it fell.',
  },
  {
    name: 'log_return',
    label: 'Log return',
    description: 'Logarithmic version of daily return, often used in financial modelling.',
    howToRead: 'Interpret it like daily return; it is more stable for modelling.',
  },
  {
    name: 'volatility_5d',
    label: 'Five-session volatility',
    description: 'Standard deviation of daily returns over the most recent five sessions.',
    howToRead: 'Higher values mean larger recent price swings and more uncertainty.',
  },
  {
    name: 'return_lag_1',
    label: 'One-session return lag',
    description: 'The market return from one session ago.',
    howToRead: 'Helps the model test whether recent momentum continues or reverses.',
  },
  {
    name: 'return_lag_3',
    label: 'Three-session return lag',
    description: 'The market return from three sessions ago.',
    howToRead: 'Captures a short-term momentum pattern without using future data.',
  },
  {
    name: 'return_lag_5',
    label: 'Five-session return lag',
    description: 'The market return from five sessions ago.',
    howToRead: 'Shows whether a slightly longer recent move has predictive value.',
  },
  {
    name: 'next_day_return',
    label: 'Next-day return target',
    description: 'The return that occurred on the following session. This is the regression target, not an input.',
    howToRead: 'The model tries to estimate this value from earlier information.',
  },
  {
    name: 'next_day_direction',
    label: 'Next-day direction target',
    description: 'Whether the following session return was positive (1) or negative (0). This is the classification target.',
    howToRead: 'Used to train Up/Down models; it is never used as an input for the same prediction.',
  },
];

const TREND_TERMS: Record<string, string> = {
  stock_market: 'stock market',
  inflation: 'inflation',
  interest_rates: 'interest rates',
  unemployment: 'unemployment',
  recession: 'recession',
};

const TREND_SUFFIXES: Array<{ suffix: string; label: string; description: string; howToRead: string }> = [
  {
    suffix: '_trend',
    label: 'Search-interest level',
    description: 'Google Trends interest for the topic on the same date, aligned to the market session.',
    howToRead: '0–100 relative interest; it is not a percentage of people searching.',
  },
  {
    suffix: '_trend_lag_1',
    label: 'One-session search lag',
    description: 'Search interest from one session earlier.',
    howToRead: 'Tests whether attention leads the market by one session.',
  },
  {
    suffix: '_trend_lag_3',
    label: 'Three-session search lag',
    description: 'Search interest from three sessions earlier.',
    howToRead: 'Tests a medium short-term lead relationship.',
  },
  {
    suffix: '_trend_lag_7',
    label: 'Seven-session search lag',
    description: 'Search interest from seven sessions earlier.',
    howToRead: 'Tests whether attention precedes market movement over a longer window.',
  },
  {
    suffix: '_trend_change',
    label: 'Search-interest change',
    description: 'Change in Google Trends interest from the previous session.',
    howToRead: 'Positive means interest increased; negative means it decreased.',
  },
];

function topicFromFeature(featureName: string): string {
  for (const key of Object.keys(TREND_TERMS)) {
    if (featureName.startsWith(`${key}_`)) return TREND_TERMS[key];
  }
  return 'configured topic';
}

export function getFeatureDefinition(featureName: string): FeatureDefinition {
  const exact = FEATURE_DEFINITIONS.find((feature) => feature.name === featureName);
  if (exact) return exact;

  for (const item of TREND_SUFFIXES) {
    if (featureName.endsWith(item.suffix)) {
      const topic = topicFromFeature(featureName);
      return {
        name: featureName,
        label: `${topic} ${item.label}`,
        description: item.description,
        howToRead: item.howToRead,
      };
    }
  }

  return {
    name: featureName,
    label: featureName.replaceAll('_', ' '),
    description: 'An engineered input created from historical market or search-interest data.',
    howToRead: 'Check the Statistics page to see its historical relationship with the target.',
  };
}

interface FeatureGlossaryProps {
  features?: string[];
  title?: string;
  compact?: boolean;
}

export default function FeatureGlossary({ features, title = 'Feature guide', compact = false }: FeatureGlossaryProps) {
  const [query, setQuery] = useState('');
  const uniqueFeatures = useMemo(() => Array.from(new Set(features ?? [])), [features]);
  const definitions = useMemo(() => {
    const source = uniqueFeatures.length ? uniqueFeatures.map(getFeatureDefinition) : FEATURE_DEFINITIONS;
    const normalizedQuery = query.trim().toLowerCase();
    return source
      .filter((feature) => !normalizedQuery || `${feature.name} ${feature.label} ${feature.description}`.toLowerCase().includes(normalizedQuery))
      .sort((a, b) => a.label.localeCompare(b.label));
  }, [query, uniqueFeatures]);

  return (
    <section className={`rounded-lg border border-gray-200 bg-white p-5 shadow-sm ${compact ? '' : 'space-y-4'}`}>
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h3 className="text-lg font-semibold text-gray-900">{title}</h3>
          <p className="mt-1 text-sm text-gray-600">What each input means and how to interpret it.</p>
        </div>
        {uniqueFeatures.length > 4 && (
          <input
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder="Filter features..."
            className="rounded-md border border-gray-300 px-3 py-2 text-sm"
            aria-label="Filter features"
          />
        )}
      </div>

      <div className={compact ? 'grid grid-cols-1 gap-3 md:grid-cols-2' : 'grid grid-cols-1 gap-3 lg:grid-cols-2'}>
        {definitions.map((feature) => (
          <article key={feature.name} className="rounded-md border border-gray-100 bg-gray-50 p-4">
            <div className="flex items-start justify-between gap-3">
              <div>
                <h4 className="text-sm font-semibold text-gray-900">{feature.label}</h4>
                <p className="mt-1 text-xs text-gray-500 break-all">{feature.name}</p>
              </div>
              {feature.name.includes('_trend') && <span className="rounded-full bg-green-50 px-2 py-1 text-xs font-medium text-green-700">Trends</span>}
            </div>
            <p className="mt-3 text-sm text-gray-700">{feature.description}</p>
            <p className="mt-2 text-sm text-gray-600"><span className="font-semibold text-gray-700">How to read: </span>{feature.howToRead}</p>
          </article>
        ))}
      </div>
      {definitions.length === 0 && <p className="text-sm text-gray-500">No features match this filter.</p>}
    </section>
  );
}
