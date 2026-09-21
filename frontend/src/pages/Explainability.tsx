import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { fetchModelRuns, explainModel } from '../services/api';
import type { ModelRun, ExplainabilityResponse } from '../types/api';
import { useState } from 'react';

const DEFAULT_SYMBOL = '^NSEI';
const DEFAULT_DATE = '2024-06-27';

export default function Explainability() {
  const queryClient = useQueryClient();
  const [selectedModelId, setSelectedModelId] = useState<number | ''>('');
  const [symbol, setSymbol] = useState(DEFAULT_SYMBOL);
  const [predictionDate, setPredictionDate] = useState(DEFAULT_DATE);

  const { data: models, isLoading: modelsLoading } = useQuery({
    queryKey: ['modelRuns'],
    queryFn: () => fetchModelRuns(),
  });

  const { data: explanation, isLoading: explanationLoading, error: explanationError } = useQuery({
    queryKey: ['explainability', selectedModelId, symbol, predictionDate],
    queryFn: () => explainModel({ model_run_id: Number(selectedModelId), symbol, prediction_date: predictionDate }),
    enabled: !!selectedModelId,
  });

  return (
    <div className="space-y-6">
      <section>
        <h2 className="text-xl font-semibold text-gray-900">Model Explainability</h2>
        <p className="mt-1 text-sm text-gray-500">SHAP-based feature importance for model predictions</p>
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
      </section>

      {explanationError && (
        <p className="text-sm text-red-600">Failed to load explanation: {String(explanationError)}</p>
      )}

      {explanation && (
        <section className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm space-y-6">
          <div>
            <h3 className="text-lg font-semibold text-gray-900">Prediction Summary</h3>
            <div className="mt-4 grid grid-cols-1 gap-4 sm:grid-cols-3">
              <Info label="Model" value={explanation.model_name} />
              <Info label="Task" value={explanation.task_type} />
              <Info label="Date" value={explanation.prediction_date} />
              {explanation.predicted_class !== null && (
                <Info label="Predicted Class" value={String(explanation.predicted_class)} />
              )}
              {explanation.predicted_return !== null && (
                <Info label="Predicted Return" value={`${(explanation.predicted_return * 100).toFixed(3)}%`} />
              )}
              {explanation.predicted_direction && (
                <Info label="Direction" value={explanation.predicted_direction} />
              )}
            </div>
          </div>

          <div>
            <h3 className="text-lg font-semibold text-gray-900">Top Features (SHAP)</h3>
            <div className="mt-4 space-y-3">
              {explanation.top_features.map((item) => (
                <div key={item.feature} className="flex items-center gap-4">
                  <div className="w-48 truncate text-sm text-gray-700">{item.feature}</div>
                  <div className="flex-1">
                    <div className="h-2 rounded-full bg-gray-100">
                      <div
                        className={`h-2 rounded-full ${item.shap_value >= 0 ? 'bg-blue-500' : 'bg-red-500'}`}
                        style={{ width: `${Math.min(100, Math.abs(item.shap_value) * 100)}%` }}
                      />
                    </div>
                  </div>
                  <div className="w-24 text-right text-sm text-gray-600">{item.shap_value.toFixed(4)}</div>
                </div>
              ))}
            </div>
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
