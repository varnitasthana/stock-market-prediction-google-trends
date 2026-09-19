import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { fetchModelRuns, predict } from '../services/api';
import type { ClassificationPredictionResponse, RegressionPredictionResponse, ModelRun } from '../types/api';
import { useState } from 'react';

const DEFAULT_SYMBOL = '^NSEI';

export default function Predictions() {
  const queryClient = useQueryClient();
  const [selectedModelId, setSelectedModelId] = useState<number | ''>('');
  const [symbol, setSymbol] = useState(DEFAULT_SYMBOL);
  const [predictionDate, setPredictionDate] = useState('2024-06-27');

  const { data: models, isLoading: modelsLoading } = useQuery({
    queryKey: ['modelRuns'],
    queryFn: () => fetchModelRuns(),
  });

  const predictionMutation = useMutation({
    mutationFn: () =>
      predict({
        model_run_id: Number(selectedModelId),
        symbol,
        prediction_date: predictionDate,
      }),
  });

  const result = predictionMutation.data as (ClassificationPredictionResponse | RegressionPredictionResponse) | undefined;
  const isClassification = result?.task_type === 'classification';

  return (
    <div className="space-y-6">
      <section>
        <h2 className="text-xl font-semibold text-gray-900">Prediction</h2>
        <p className="mt-1 text-sm text-gray-500">Generate a historical prediction using a trained model</p>
      </section>

      <section className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm">
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
          <div>
            <label className="block text-sm font-medium text-gray-700">Model Run</label>
            <select
              value={selectedModelId}
              onChange={(e) => setSelectedModelId(e.target.value ? Number(e.target.value) : '')}
              className="mt-1 rounded-md border border-gray-300 px-3 py-2 text-sm"
            >
              <option value="">Select a trained model</option>
              {models?.map((model: ModelRun) => (
                <option key={model.id} value={model.id}>
                  {model.model_name} ({model.task_type}) — Run #{model.id}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700">Symbol</label>
            <input value={symbol} onChange={(e) => setSymbol(e.target.value)} className="mt-1 rounded-md border border-gray-300 px-3 py-2 text-sm" />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700">Prediction Date</label>
            <input type="date" value={predictionDate} onChange={(e) => setPredictionDate(e.target.value)} className="mt-1 rounded-md border border-gray-300 px-3 py-2 text-sm" />
          </div>
        </div>
        <div className="mt-4">
          <button
            onClick={() => predictionMutation.mutate()}
            disabled={!selectedModelId || predictionMutation.isPending}
            className="rounded-md bg-blue-600 px-4 py-2 text-sm font-semibold text-white hover:bg-blue-500 disabled:opacity-50"
          >
            {predictionMutation.isPending ? 'Generating...' : 'Generate Prediction'}
          </button>
        </div>
      </section>

      {predictionMutation.isError && (
        <p className="text-sm text-red-600">Prediction failed: {String(predictionMutation.error)}</p>
      )}

      {result && (
        <section className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm">
          <h3 className="text-lg font-semibold text-gray-900">Prediction Result</h3>
          <div className="mt-4 grid grid-cols-1 gap-4 sm:grid-cols-2">
            <Info label="Model Run ID" value={String(result.model_run_id)} />
            <Info label="Model" value={result.model_name} />
            <Info label="Task" value={result.task_type} />
            <Info label="Symbol" value={result.symbol} />
            <Info label="Date" value={result.prediction_date} />
            <Info label="Target" value={result.target_name} />
          </div>
          <div className="mt-4 rounded-md bg-gray-50 p-4">
            {isClassification ? (
              <div className="space-y-2">
                <p className="text-sm text-gray-500">Predicted Direction</p>
                <p className="text-3xl font-semibold text-gray-900">{(result as ClassificationPredictionResponse).predicted_direction}</p>
                <p className="text-sm text-gray-600">Class: {(result as ClassificationPredictionResponse).predicted_class}</p>
                <div className="flex gap-4 text-sm">
                  <span>Down: {((result as ClassificationPredictionResponse).probability_down ?? 0 * 100).toFixed(1)}%</span>
                  <span>Up: {((result as ClassificationPredictionResponse).probability_up ?? 0 * 100).toFixed(1)}%</span>
                </div>
              </div>
            ) : (
              <div className="space-y-2">
                <p className="text-sm text-gray-500">Predicted Next-Day Return</p>
                <p className="text-3xl font-semibold text-gray-900">{((result as RegressionPredictionResponse).predicted_return * 100).toFixed(3)}%</p>
              </div>
            )}
          </div>
        </section>
      )}
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
