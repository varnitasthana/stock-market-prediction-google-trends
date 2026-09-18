function App() {
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
        <div className="rounded-lg border-2 border-dashed border-gray-300 p-12 text-center">
          <h2 className="text-xl font-semibold text-gray-700">Dashboard</h2>
          <p className="mt-2 text-gray-500">Frontend implementation in progress. Connect to the FastAPI backend at http://localhost:8000</p>
        </div>
      </main>
    </div>
  )
}

export default App
