import { useState } from 'react'
import { useDashboardSummary } from './hooks/useApi'

const DEFAULT_SYMBOL = 'NSEI'

function App() {
  const [symbol, setSymbol] = useState(DEFAULT_SYMBOL)
  const [input, setInput] = useState(DEFAULT_SYMBOL)
  const { data, isLoading, error, refetch } = useDashboardSummary(symbol)

  const submit = (e: React.FormEvent) => {
    e.preventDefault()
    const trimmed = input.trim().toUpperCase()
    if (trimmed) {
      setSymbol(trimmed)
    }
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white shadow">
        <div className="mx-auto max-w-7xl px-4 py-6 sm:px-6 lg:px-8">
          <h1 className="text-3xl font-bold tracking-tight text-gray-900">
            Stock Market Behaviour Prediction System
          </h1>
          <p className="mt-1 text-sm text-gray-500">
            Analyzing Google Trends as an indicator of market behaviour
          </p>
        </div>
      </header>
      <main className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
        <div className="mb-6 rounded-md bg-yellow-50 p-4 text-sm text-yellow-800">
          If you see this text, the updated frontend is loaded. Previous placeholder should be gone now.
        </div>
        <form onSubmit={submit} className="mb-6 flex items-center gap-3">
          <label htmlFor="symbol" className="text-sm font-medium text-gray-700">
            Symbol
          </label>
          <input
            id="symbol"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="e.g. NSEI"
            className="rounded-md border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
          />
          <button
            type="submit"
            className="rounded-md bg-blue-600 px-4 py-2 text-sm font-semibold text-white hover:bg-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
          >
            Load
          </button>
          <button
            type="button"
            onClick={() => refetch()}
            className="rounded-md border border-gray-300 px-4 py-2 text-sm font-semibold text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
          >
            Refresh
          </button>
        </form>

        {isLoading && <p className="text-gray-600">Loading dashboard...</p>}
        {error && <p className="text-red-600">Failed to load dashboard: {String(error)}</p>}

        {data && (
          <div className="grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-3">
            <DashboardCard title="Symbol" value={data.symbol} />
            <DashboardCard title="Latest Close" value={data.latest_close != null ? Number(data.latest_close).toFixed(2) : 'N/A'} />
            <DashboardCard title="Latest Date" value={data.latest_date ?? 'N/A'} />
            <DashboardCard title="Daily Return" value={data.latest_daily_return != null ? Number(data.latest_daily_return).toFixed(4) : 'N/A'} />
            <DashboardCard title="Latest Model" value={data.latest_model ?? 'N/A'} />
            <DashboardCard title="Last Training Date" value={data.last_training_date ?? 'N/A'} />
            <DashboardCard title="Prediction Direction" value={data.prediction_direction != null ? String(data.prediction_direction) : 'N/A'} />
            <DashboardCard title="Prediction Probability" value={data.prediction_probability != null ? Number(data.prediction_probability).toFixed(4) : 'N/A'} />
            <DashboardCard title="Prediction Date" value={data.prediction_date ?? 'N/A'} />
          </div>
        )}
      </main>
    </div>
  )
}

function DashboardCard({ title, value }: { title: string; value: string | number }) {
  return (
    <div className="rounded-lg border border-gray-200 bg-white p-5 shadow-sm">
      <p className="text-sm font-medium text-gray-500">{title}</p>
      <p className="mt-2 text-2xl font-semibold text-gray-900">{value}</p>
    </div>
  )
}

export default App
