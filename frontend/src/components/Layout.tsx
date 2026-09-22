import { ReactNode } from 'react';

type Page = 'dashboard' | 'data' | 'statistics' | 'models' | 'predictions' | 'explainability' | 'sentiment' | 'guide';

interface LayoutProps {
  currentPage: Page;
  onNavigate: (page: Page) => void;
  children: ReactNode;
}

const NAV_ITEMS: { page: Page; label: string; description: string }[] = [
  { page: 'dashboard', label: 'Dashboard', description: 'Data health and project overview' },
  { page: 'data', label: 'Data Explorer', description: 'Historical market and Trends charts' },
  { page: 'statistics', label: 'Statistics', description: 'Correlation, lag, and pattern analysis' },
  { page: 'models', label: 'Models', description: 'Train and evaluate machine-learning models' },
  { page: 'predictions', label: 'Predictions', description: 'Estimate a historical session outcome' },
  { page: 'explainability', label: 'Explainability', description: 'See what influenced a model output' },
  { page: 'sentiment', label: 'Sentiment', description: 'Read simple market and text sentiment' },
  { page: 'guide', label: 'Guide', description: 'Learn how to use every feature' },
];

export default function Layout({ currentPage, onNavigate, children }: LayoutProps) {
  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white shadow">
        <div className="mx-auto max-w-7xl px-4 py-6 sm:px-6 lg:px-8">
          <h1 className="text-2xl font-bold tracking-tight text-gray-900">Stock Market Behaviour Prediction System</h1>
          <p className="mt-1 text-sm text-gray-500">Explore historical data, understand patterns, and interpret model outputs with guided explanations.</p>
        </div>
      </header>
      <nav className="bg-white border-b border-gray-200">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="flex gap-6 overflow-x-auto">
            {NAV_ITEMS.map((item) => (
              <button
                key={item.page}
                onClick={() => onNavigate(item.page)}
                title={item.description}
                aria-label={`${item.label}: ${item.description}`}
                className={`whitespace-nowrap border-b-2 px-1 py-4 text-sm font-medium ${
                  currentPage === item.page
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-700'
                }`}
              >
                {item.label}
              </button>
            ))}
          </div>
        </div>
      </nav>
      <main className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">{children}</main>
      <footer className="mx-auto max-w-7xl px-4 py-6 sm:px-6 lg:px-8">
        <p className="text-center text-xs text-gray-400">
          This project is an educational and research-oriented machine learning system. Its predictions are based on historical data and should not be interpreted as investment advice or a guarantee of future market performance.
        </p>
      </footer>
    </div>
  );
}
