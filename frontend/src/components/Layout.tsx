import { ReactNode } from 'react';

type Page = 'dashboard' | 'data' | 'statistics' | 'models' | 'predictions' | 'explainability' | 'sentiment';

interface LayoutProps {
  currentPage: Page;
  onNavigate: (page: Page) => void;
  children: ReactNode;
}

const NAV_ITEMS: { page: Page; label: string }[] = [
  { page: 'dashboard', label: 'Dashboard' },
  { page: 'data', label: 'Data' },
  { page: 'statistics', label: 'Statistics' },
  { page: 'models', label: 'Models' },
  { page: 'predictions', label: 'Predictions' },
  { page: 'explainability', label: 'Explainability' },
  { page: 'sentiment', label: 'Sentiment' },
];

export default function Layout({ currentPage, onNavigate, children }: LayoutProps) {
  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white shadow">
        <div className="mx-auto max-w-7xl px-4 py-6 sm:px-6 lg:px-8">
          <h1 className="text-2xl font-bold tracking-tight text-gray-900">Stock Market Behaviour Prediction System</h1>
          <p className="mt-1 text-sm text-gray-500">Google Trends + NIFTY 50 + Sentiment + Explainability</p>
        </div>
      </header>
      <nav className="bg-white border-b border-gray-200">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="flex gap-6 overflow-x-auto">
            {NAV_ITEMS.map((item) => (
              <button
                key={item.page}
                onClick={() => onNavigate(item.page)}
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
