import { useState } from 'react';
import Layout from './components/Layout';
import Dashboard from './pages/Dashboard';
import DataExplorer from './pages/DataExplorer';
import Statistics from './pages/Statistics';
import Models from './pages/Models';
import Predictions from './pages/Predictions';
import Explainability from './pages/Explainability';
import Sentiment from './pages/Sentiment';

type Page = 'dashboard' | 'data' | 'statistics' | 'models' | 'predictions' | 'explainability' | 'sentiment';

const DEFAULT_SYMBOL = '^NSEI';

function App() {
  const [page, setPage] = useState<Page>('dashboard');
  const [symbol, setSymbol] = useState(DEFAULT_SYMBOL);

  const navigate = (target: Page) => {
    setPage(target);
  };

  return (
    <Layout currentPage={page} onNavigate={navigate}>
      {page === 'dashboard' && <Dashboard symbol={symbol} />}
      {page === 'data' && <DataExplorer />}
      {page === 'statistics' && <Statistics />}
      {page === 'models' && <Models />}
      {page === 'predictions' && <Predictions />}
      {page === 'explainability' && <Explainability />}
      {page === 'sentiment' && <Sentiment />}
    </Layout>
  );
}

export default App
