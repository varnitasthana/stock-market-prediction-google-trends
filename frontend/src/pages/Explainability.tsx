import { useMemo, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { explainModel, fetchMarketDataStatus, fetchModelRuns } from '../services/api';
import type { MarketDataStatusResponse, ModelRun } from '../types/api';
import FeatureGlossary from '../components/FeatureGlossary';
import HelpPanel from '../components/HelpPanel';
import PageIntro from '../components/PageIntro';
import StatusBadge from '../components/StatusBadge';
import { formatDisplayDate, getTodayISO } from '../utils/date';

const DEFAULT_SYMBOL = '^NSEI';

function StatusOverview({ status, loading }: { status?: MarketDataStatusResponse | null; loading: boolean }) {
  if (loading) {
    return <StatusBadge label="Checking market status" />;
  }

  if (!status) {
    return <StatusBadge label="Using safe date defaults" tone="warning" />;
  }

  return (
    <div className="flex flex-wrap gap-2">
      <StatusBadge label={`Today: ${formatDisplayDate(status.today)}`} />
      <StatusBadge label={`Expected Session: ${formatDisplayDate(status.expected_session)}`} tone={status.is_stale ? 'warning' : 'success'} />
      <StatusBadge label={`Latest Stored Session: ${formatDisplayDate(status.last_stored_date)}`} tone={status.is_stale ? 'warning' : 'success'} />
    </div>
  );
}

export default function Explainability() {
  const [selectedModelId, setSelectedModelId] = useState<number | ''>('');
  const [symbol, setSymbol] = useState(DEFAULT_SYMBOL);
  const [predictionDate, setPredictionDate] = useState('');

  const { data: marketStatus, isLoading: statusLoading, error: statusError } = useQuery({
    queryKey: ['marketStatus', DEFAULT_SYMBOL],
    queryFn: () => fetchMarketDataStatus(DEFAULT_SYMBOL),
  });

  const safePredictionDate = marketStatus?.last_stored_date ?? marketStatus?.expected_session ?? getTodayISO();

  const { data: models, isLoading: modelsLoading, error: modelsError } = useQuery({
    queryKey: ['modelRuns'],
    queryFn: () => fetchModelRuns(),
  });

  const { data: explanation, isLoading: explanationLoading, error: explanationError, isFetching } = useQuery({
    queryKey: ['explainability', selectedModelId, symbol.trim(), predictionDate],
    queryFn: () => explainModel({
      model_run_id: Number(selectedModelId),
      symbol: symbol.trim(),
      prediction_date: predictionDate || safePredictionDate,
    }),
    enabled: !!selectedModelId && !!symbol.trim() && !!(predictionDate || safePredictionDate),
  });

  const selectedModel = models?.find((model: ModelRun) => model.id === selectedModelId);
  const featureNames = useMemo(() => explanation?.top_features.map((item) => item.feature) ?? [], [explanation]);
  const maxAbsoluteShap = useMemo(() => {
    const values = explanation?.top_features.map((item) => Math.abs(item.shap_value)) ?? [];
    return values.length ? Math.max(...values) : 0;
  }, [explanation]);
  const canExplain = !!selectedModelId && !!symbol.trim() && !!predictionDate && !explanationLoading;

  return (
    <div className="space-y-6" aria-live="polite">
      <PageIntro
        title="Model Explainability"
        description="Inspect why a trained model produced a prediction for a stored historical session."
      >
        <StatusOverview status={marketStatus} loading={statusLoading} />
      </PageIntro>

      <HelpPanel title="How to read model explanations">
        <p><strong>Purpose:</strong> Show which stored input features pushed an individual prediction upward or downward.</p>
        <p><strong>Inputs:</strong> A persisted model run, a matching symbol, and a Historical Prediction Date with engineered feature values.</p>
        <p><strong>Outputs:</strong> The prediction summary and the leading features ranked by absolute SHAP value.</p>
        <p><strong>Interpretation:</strong> A positive SHAP value increased the model output; a negative value decreased it. The bar length shows relative influence within the displayed features.</p>
        <p><strong>Limitations:</strong> SHAP explains the model behavior, not market causality. Values depend on the selected model, date, feature pipeline, and training sample.</p>
        <p><strong>Historical patterns:</strong> Compare explanations across several dates and market directions, then check Statistics for broader historical associations.</p>
      </HelpPanel>

      {statusError && (
        <p role="alert" className="rounded-md border border-red-200 bg-red-50 p-3 text-sm text-red-700">
          Market status could not be loaded. Safe date defaults are being used. {String(statusError)}
        </p>
      )}

      {marketStatus?.message && (
        <div className="rounded-md border border-blue-200 bg-blue-50 p-4 text-sm text-blue-900">
          <p className="font-semibold">Stored data notice</p>
          <p className="mt-1">{marketStatus.message}</p>
        </div>
      )}

      <section className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <h3 className="text-lg font-semibold text-gray-900">Explanation Inputs</h3>
            <p className="mt-1 text-sm text-gray-600">Choose a historical session for a local, prediction-level explanation.</p>
          </div>
          <StatusBadge label={`Historical Prediction Date: ${formatDisplayDate(predictionDate || safePredictionDate)}`} />
        </div>

        <div className="mt-5 grid grid-cols-1 gap-4 sm:grid-cols-3">
          <div>
            <label htmlFor="explanation-model" className="block text-sm font-medium text-gray-700">Trained model run</label>
            <select
              id="explanation-model"
              value={selectedModelId}
              onChange={(event) => setSelectedModelId(event.target.value ? Number(event.target.value) : '')}
              disabled={modelsLoading}
              className="mt-1 w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
              aria-describedby="explanation-model-help"
            >
              <option value="">Select a trained model</option>
              {models?.map((model: ModelRun) => (
                <option key={model.id} value={model.id}>
                  {model.model_name.split('_').join(' ')} ({model.task_type ?? 'unknown'}) - Run #{model.id}
                </option>
              ))}
            </select>
            <p id="explanation-model-help" className="mt-1 text-xs text-gray-500">
              {modelsLoading ? 'Loading model runs...' : modelsError ? 'Model runs are unavailable.' : `${models?.length ?? 0} run(s) available`}
            </p>
          </div>
          <div>
            <label htmlFor="explanation-symbol" className="block text-sm font-medium text-gray-700">Market symbol</label>
            <input
              id="explanation-symbol"
              value={symbol}
              onChange={(event) => setSymbol(event.target.value)}
              className="mt-1 w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
              aria-describedby="explanation-symbol-help"
            />
            <p id="explanation-symbol-help" className="mt-1 text-xs text-gray-500">Use the same symbol that was used to train the selected model.</p>
          </div>
          <div>
            <label htmlFor="explanation-date" className="block text-sm font-medium text-gray-700">Historical prediction date</label>
            <input
              id="explanation-date"
              type="date"
              value={predictionDate || safePredictionDate}
              onChange={(event) => setPredictionDate(event.target.value)}
              min={marketStatus?.first_stored_date}
              max={marketStatus?.last_stored_date ?? marketStatus?.expected_session}
              className="mt-1 w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
              aria-describedby="explanation-date-help"
            />
            <p id="explanation-date-help" className="mt-1 text-xs text-gray-500">
              {statusLoading ? 'Loading stored date range...' : `Stored context: ${formatDisplayDate(marketStatus?.first_stored_date)} to ${formatDisplayDate(safePredictionDate)}`}
            </p>
          </div>
        </div>

        <div className="mt-4 flex flex-wrap items-center gap-3">
          <StatusBadge label={canExplain ? 'Ready to explain' : 'Select valid inputs'} tone={canExplain ? 'success' : 'neutral'} />
          <p className="text-xs text-gray-500">
            {!selectedModelId ? 'Choose a model run first.' : selectedModel?.symbol !== symbol.trim() ? 'The symbol must match the selected model.' : 'The explanation uses features stored for the selected historical date.'}
          </p>
        </div>

        {modelsError && (
          <p role="alert" className="mt-4 rounded-md border border-red-200 bg-red-50 p-3 text-sm text-red-700">
            Failed to load trained models. {String(modelsError)}
          </p>
        )}
        {!modelsLoading && !modelsError && models?.length === 0 && (
          <p className="mt-4 rounded-md border border-gray-200 bg-gray-50 p-4 text-sm text-gray-600">No trained models are available. Train a model on the Models page first.</p>
        )}
        {selectedModel && !selectedModel.artifact_path && (
          <p role="alert" className="mt-4 rounded-md border border-yellow-200 bg-yellow-50 p-3 text-sm text-yellow-800">
            This model run has no persisted artifact, so an explanation cannot be generated.
          </p>
        )}
      </section>

      {explanationLoading && (
        <p className="rounded-lg border border-gray-200 bg-white p-5 text-sm text-gray-600">Loading the model explanation...</p>
      )}
      {explanationError && (
        <p role="alert" className="rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-700">
          Failed to load the explanation. {String(explanationError)}
        </p>
      )}
      {!explanationLoading && !explanationError && selectedModelId && !explanation && !isFetching && (
        <p className="rounded-lg border border-gray-200 bg-white p-5 text-sm text-gray-600">
          No explanation is available for this model, symbol, and historical prediction date. Choose another stored date or verify that features were generated.
        </p>
      )}

      {explanation && (
        <section className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <h3 className="text-lg font-semibold text-gray-900">Prediction Summary</h3>
              <p className="mt-1 text-sm text-gray-600">Model output for the selected historical session.</p>
            </div>
            <StatusBadge label={`Historical Prediction Date: ${formatDisplayDate(explanation.prediction_date)}`} />
          </div>

          <div className="mt-4 grid grid-cols-1 gap-4 sm:grid-cols-3">
            <Info label="Model" value={explanation.model_name.split('_').join(' ')} />
            <Info label="Task" value={explanation.task_type.split('_').join(' ')} />
            <Info label="Historical Prediction Date" value={formatDisplayDate(explanation.prediction_date)} />
            {explanation.predicted_class !== null && (
              <Info label="Predicted Class" value={explanation.predicted_class === 1 ? 'Up (1)' : 'Down (0)'} />
            )}
            {explanation.predicted_return !== null && (
              <Info label="Predicted Return" value={`${(explanation.predicted_return * 100).toFixed(3)}%`} />
            )}
            {explanation.predicted_direction && (
              <Info label="Predicted Direction" value={explanation.predicted_direction} />
            )}
          </div>

          <div className="mt-6">
            <div className="flex flex-wrap items-start justify-between gap-3">
              <div>
                <h3 className="text-lg font-semibold text-gray-900">Top Features (SHAP)</h3>
                <p className="mt-1 text-sm text-gray-600">Positive values increase the output; negative values decrease it.</p>
              </div>
              <StatusBadge label={`${explanation.top_features.length} feature(s)`} />
            </div>

            {explanation.top_features.length === 0 ? (
              <p className="mt-4 rounded-md border border-gray-200 bg-gray-50 p-4 text-sm text-gray-600">The model did not return feature-level SHAP values for this prediction.</p>
            ) : (
              <div className="mt-4 space-y-4">
                {explanation.top_features.map((item) => {
                  const width = maxAbsoluteShap > 0 ? Math.max(5, (Math.abs(item.shap_value) / maxAbsoluteShap) * 100) : 0;
                  return (
                    <div key={item.feature} className="grid grid-cols-1 gap-2 sm:grid-cols-[minmax(10rem,18rem)_1fr_5rem] sm:items-center">
                      <div className="truncate text-sm font-medium text-gray-800" title={item.feature}>{item.feature.split('_').join(' ')}</div>
                      <div>
                        <div className="h-2 rounded-full bg-gray-100" role="img" aria-label={`${item.feature.split('_').join(' ')} SHAP value ${item.shap_value.toFixed(4)}`}>
                          <div
                            className={`h-2 rounded-full ${item.shap_value >= 0 ? 'bg-blue-500' : 'bg-red-500'}`}
                            style={{ width: `${width}%` }}
                          />
                        </div>
                        <p className="mt-1 text-xs text-gray-500">{item.shap_value >= 0 ? 'Increases' : 'Decreases'} the model output</p>
                      </div>
                      <div className="text-right text-sm tabular-nums text-gray-700">{item.shap_value.toFixed(4)}</div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>

          <FeatureGlossary features={featureNames} title="Explained feature guide" compact />
        </section>
      )}
    </div>
  );
}

function Info({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <p className="text-xs text-gray-500">{label}</p>
      <p className="mt-1 text-sm font-medium text-gray-900">{value}</p>
    </div>
  );
}
