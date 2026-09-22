import FeatureGlossary from '../components/FeatureGlossary';
import HelpPanel from '../components/HelpPanel';
import PageIntro from '../components/PageIntro';

const WORKFLOW = [
  {
    title: '1. Check data freshness',
    text: 'Confirm that the latest stored session is close to the expected session. Stale data can make every later result outdated.',
  },
  {
    title: '2. Explore the history',
    text: 'Compare the index close, daily return, and Google Trends interest over the same date range. Look for repeated patterns, not isolated spikes.',
  },
  {
    title: '3. Read the statistics',
    text: 'Use descriptive statistics for scale, correlations for direction, lag analysis for timing, and direction groups for context.',
  },
  {
    title: '4. Review the model',
    text: 'Check the training period, task type, evaluation metrics, and feature count before trusting a prediction.',
  },
  {
    title: '5. Interpret the output',
    text: 'A prediction is an estimate based on historical relationships. Use Explainability to see which inputs influenced that estimate.',
  },
];

export default function Guide() {
  return (
    <div className="space-y-6">
      <PageIntro
        title="How to use this application"
        description="A guided path from raw market and search-interest data to an interpretable model output."
      />

      <section className="rounded-lg border border-gray-200 bg-white p-5 shadow-sm">
        <h2 className="text-xl font-semibold text-gray-900">Recommended workflow</h2>
        <div className="mt-4 grid grid-cols-1 gap-4 lg:grid-cols-5">
          {WORKFLOW.map((step) => (
            <article key={step.title} className="rounded-md border border-gray-100 bg-gray-50 p-4">
              <h3 className="text-sm font-semibold text-gray-900">{step.title}</h3>
              <p className="mt-2 text-sm text-gray-600">{step.text}</p>
            </article>
          ))}
        </div>
      </section>

      <section className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <HelpPanel title="What the date labels mean" defaultOpen>
          <p><span className="font-semibold">Today:</span> the current calendar date in India Standard Time.</p>
          <p><span className="font-semibold">Expected session:</span> the most recent trading session that should normally be available.</p>
          <p><span className="font-semibold">Latest stored session:</span> the last date with a row in the database. This is the date used by historical analysis.</p>
          <p>If the latest stored session is behind the expected session, use the refresh button on the Dashboard. A refresh downloads available provider rows and recomputes derived metrics; it never fabricates a missing session.</p>
        </HelpPanel>

        <HelpPanel title="How to analyze a historical pattern">
          <ul className="list-disc space-y-2 pl-5">
            <li>Start with the direction and size of the market move over the full selected window.</li>
            <li>Check whether positive and negative sessions are balanced or clustered.</li>
            <li>Compare search-interest changes with market changes, while remembering that correlation is not causation.</li>
            <li>Use lag results to see whether attention tended to move before, after, or alongside market returns.</li>
            <li>Check volatility before acting on a pattern; a large return during high volatility is less stable.</li>
          </ul>
        </HelpPanel>
      </section>

      <section className="rounded-lg border border-gray-200 bg-white p-5 shadow-sm">
        <h2 className="text-xl font-semibold text-gray-900">What each page is for</h2>
        <div className="mt-4 grid grid-cols-1 gap-3 md:grid-cols-2">
          <PageCard title="Dashboard" text="A quick health check for data freshness, project coverage, and the overall pipeline." />
          <PageCard title="Data Explorer" text="Historical charts for market prices and Google Trends interest, plus a plain-language pattern summary." />
          <PageCard title="Statistics" text="Descriptive, correlation, lag, and direction-group analysis for the selected historical window." />
          <PageCard title="Models" text="Model training and evaluation controls with an explanation of classification and regression tasks." />
          <PageCard title="Predictions" text="A historical-date model estimate. The selected date must have engineered features available." />
          <PageCard title="Explainability" text="Shows which inputs influenced a model output and whether each influence moved the estimate up or down." />
          <PageCard title="Sentiment" text="A simple rule-based text sentiment check and a daily market-derived sentiment snapshot." />
        </div>
      </section>

      <FeatureGlossary title="Why these features exist" />

      <HelpPanel title="Important limitations">
        <p>Google Trends values are relative interest scores from 0 to 100, not percentages of people searching. Statistical relationships can change over time, and a model trained on one period may not generalize to another.</p>
        <p>Predictions and explanations are educational research outputs. They are not investment advice, recommendations, or guarantees of future performance.</p>
      </HelpPanel>
    </div>
  );
}

function PageCard({ title, text }: { title: string; text: string }) {
  return (
    <article className="rounded-md border border-gray-100 bg-gray-50 p-4">
      <h3 className="text-sm font-semibold text-gray-900">{title}</h3>
      <p className="mt-2 text-sm text-gray-600">{text}</p>
    </article>
  );
}
