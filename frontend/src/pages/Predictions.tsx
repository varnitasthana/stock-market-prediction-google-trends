import { useEffect, useState } from 'react';
import { useMutation, useQuery } from '@tanstack/react-query';
import { fetchMarketDataStatus, fetchModelRuns, predict } from '../services/api';
import type { ClassificationPredictionResponse, MarketDataStatusResponse, ModelRun, RegressionPredictionResponse } from '../types/api';
import FeatureGlossary from '../components/FeatureGlossary';
import HelpPanel from '../components/HelpPanel';
import PageIntro from '../components/PageIntro';
import StatusBadge from '../components/StatusBadge';
import { formatDisplayDate, getTodayISO } from '../utils/date';

const DEFAULT_SYMBOL = '^NSEI';

type PredictionResult = ClassificationPredictionResponse | RegressionPredictionResponse;

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

export default function Predictions() {
  const [selectedModelId, setSelectedModelId] = useState<number | ''>('');
  const [symbol, setSymbol] = useState(DEFAULT_SYMBOL);
  const [predictionDate, setPredictionDate] = useState('');

  const { data: marketStatus, isLoading: statusLoading, error: statusError } = useQuery({
    queryKey: ['marketStatus', DEFAULT_SYMBOL],
    queryFn: () => fetchMarketDataStatus(DEFAULT_SYMBOL),
  });

  const safePredictionDate = marketStatus?.last_stored_date ?? marketStatus?.expected_session ?? getTodayISO();
  const resolvedPredictionDate = predictionDate || safePredictionDate;
  const normalizedSymbol = symbol.trim();

  const { data: models, isLoading: modelsLoading, error: modelsError } = useQuery({
    queryKey: ['modelRuns'],
    queryFn: () => fetchModelRuns(),
  });

  const predictionMutation = useMutation({
    mutationFn: () => {
      if (!selectedModelId) throw new Error('Select a trained model before generating a prediction.');
      return predict({
        model_run_id: Number(selectedModelId),
        symbol: normalizedSymbol,
        prediction_date: resolvedPredictionDate,
      });
    },
  });

  useEffect(() => {
    predictionMutation.reset();
  }, [selectedModelId, symbol, predictionDate]);

  const result = predictionMutation.data as PredictionResult | undefined;
  const isClassification = result?.task_type === 'classification';
  const selectedModel = models?.find((model: ModelRun) => model.id === selectedModelId);
  const selectedSymbolMatches = !selectedModel || selectedModel.symbol === normalizedSymbol;
  const canPredict = !!selectedModelId && !!normalizedSymbol && !!resolvedPredictionDate && selectedSymbolMatches && !!selectedModel?.artifact_path && !predictionMutation.isPending;

  return (
    <div className="space-y-6" aria-live="polite">
      <PageIntro
        title="Historical Predictions"
        description="Generate a prediction for a stored historical session using a trained model."
      >
        <StatusOverview status={marketStatus} loading={statusLoading} />
      </PageIntro>

      <HelpPanel title="How to read a historical prediction">
        <p><strong>Purpose:</strong> Replay a trained model on a session that already has engineered feature data.</p>
        <p><strong>Inputs:</strong> A persisted model run, a symbol matching that run, and a Historical Prediction Date from stored market coverage.</p>
        <p><strong>Outputs:</strong> A predicted direction and class probabilities for classification, or a predicted next-session return for regression.</p>
        <p><strong>Interpretation:</strong> The result is a model estimate for the selected historical date, not a live quote or a guarantee about the next session.</p>
        <p><strong>Limitations:</strong> A date without engineered features cannot be predicted. Model errors, stale inputs, and regime changes can make the estimate inaccurate.</p>
        <p><strong>Historical patterns:</strong> Compare predictions across several dates and models, then review actual outcomes and Explainability before drawing a conclusion.</p>
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
            <h3 className="text-lg font-semibold text-gray-900">Prediction Inputs</h3>
            <p className="mt-1 text-sm text-gray-600">The date selector is limited to the stored-data context returned by the API.</p>
          </div>
          <StatusBadge label={`Historical Prediction Date: ${formatDisplayDate(predictionDate || safePredictionDate)}`} tone="neutral" />
        </div>

        <div className="mt-5 grid grid-cols-1 gap-4 sm:grid-cols-3">
          <div>
            <label htmlFor="prediction-model" className="block text-sm font-medium text-gray-700">Trained model run</label>
            <select
              id="prediction-model"
              value={selectedModelId}
              onChange={(event) => setSelectedModelId(event.target.value ? Number(event.target.value) : '')}
              disabled={modelsLoading}
              className="mt-1 w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
              aria-describedby="prediction-model-help"
            >
              <option value="">Select a trained model</option>
              {models?.map((model: ModelRun) => (
                <option key={model.id} value={model.id}>
                  {model.model_name.split('_').join(' ')} ({model.task_type ?? 'unknown'}) - Run #{model.id}
                </option>
              ))}
            </select>
            <p id="prediction-model-help" className="mt-1 text-xs text-gray-500">
              {modelsLoading ? 'Loading model runs...' : modelsError ? 'Model runs are unavailable.' : `${models?.length ?? 0} run(s) available`}
            </p>
          </div>
          <div>
            <label htmlFor="prediction-symbol" className="block text-sm font-medium text-gray-700">Market symbol</label>
            <input
              id="prediction-symbol"
              value={symbol}
              onChange={(event) => setSymbol(event.target.value)}
              className="mt-1 w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
              aria-describedby="prediction-symbol-help"
            />
            <p id="prediction-symbol-help" className="mt-1 text-xs text-gray-500">Use the same symbol that was used to train the selected model.</p>
          </div>
          <div>
            <label htmlFor="prediction-date" className="block text-sm font-medium text-gray-700">Historical prediction date</label>
            <input
              id="prediction-date"
              type="date"
              value={predictionDate || safePredictionDate}
              onChange={(event) => setPredictionDate(event.target.value)}
              min={marketStatus?.first_stored_date}
              max={marketStatus?.last_stored_date ?? marketStatus?.expected_session}
              className="mt-1 w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
              aria-describedby="prediction-date-help"
            />
            <p id="prediction-date-help" className="mt-1 text-xs text-gray-500">
              {statusLoading ? 'Loading stored date range...' : `Stored context: ${formatDisplayDate(marketStatus?.first_stored_date)} to ${formatDisplayDate(safePredictionDate)}`}
            </p>
          </div>
        </div>

        <div className="mt-4 flex flex-wrap items-center gap-3">
          <button
            type="button"
            onClick={() => predictionMutation.mutate()}
            disabled={!canPredict}
            className="rounded-md bg-blue-600 px-4 py-2 text-sm font-semibold text-white hover:bg-blue-500 disabled:cursor-not-allowed disabled:opacity-50"
            aria-describedby="predict-help"
          >
            {predictionMutation.isPending ? 'Generating...' : 'Generate Historical Prediction'}
          </button>
          <p id="predict-help" className="text-xs text-gray-500">
            {!selectedModelId ? 'Choose a model run first.' : selectedModel?.symbol !== normalizedSymbol ? 'The symbol must match the selected model.' : 'The model will use features stored for the selected date.'}
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
        {predictionMutation.isError && (
          <p role="alert" className="mt-4 rounded-md border border-red-200 bg-red-50 p-3 text-sm text-red-700">
            Prediction failed. {String(predictionMutation.error)}
          </p>
        )}
      </section>

      {result && (
        <section className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <h3 className="text-lg font-semibold text-gray-900">Prediction Result</h3>
              <p className="mt-1 text-sm text-gray-600">Estimate for the selected historical session.</p>
            </div>
            <StatusBadge label={`Historical Prediction Date: ${formatDisplayDate(result.prediction_date)}`} />
          </div>

          <div className="mt-4 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
            <Info label="Model Run ID" value={String(result.model_run_id)} />
            <Info label="Model" value={result.model_name.split('_').join(' ')} />
            <Info label="Task" value={result.task_type.split('_').join(' ')} />
            <Info label="Symbol" value={result.symbol} />
            <Info label="Historical Prediction Date" value={formatDisplayDate(result.prediction_date)} />
            <Info label="Target" value={result.target_name.split('_').join(' ')} />
          </div>

          <div className="mt-5 rounded-md bg-gray-50 p-4">
            {isClassification ? (
              <ClassificationResult result={result as ClassificationPredictionResponse} />
            ) : (
              <RegressionResult result={result as RegressionPredictionResponse} />
            )}
          </div>

          <FeatureGlossary features={result.feature_columns ?? []} title="Features used for this prediction" compact />
        </section>
      )}
    </div>
  );
}

function ClassificationResult({ result }: { result: ClassificationPredictionResponse }) {
  const down = result.probability_down ?? 0;
  const up = result.probability_up ?? 0;

  return (
    <div className="space-y-3">
      <div>
        <p className="text-sm text-gray-500">Predicted Direction</p>
        <p className="text-3xl font-semibold text-gray-900">{result.predicted_direction}</p>
        <p className="text-sm text-gray-600">Predicted class: {result.predicted_class === 1 ? 'Up (1)' : 'Down (0)'}</p>
      </div>
      <ProbabilityBar label="Down probability" value={down} tone="red" />
      <ProbabilityBar label="Up probability" value={up} tone="green" />
      <p className="text-xs text-gray-500">Probabilities are shown as percentages and may not sum to exactly 100% when the model does not provide them.</p>
    </div>
  );
}

function RegressionResult({ result }: { result: RegressionPredictionResponse }) {
  return (
    <div className="space-y-2">
      <p className="text-sm text-gray-500">Predicted Next-Session Return</p>
      <p className="text-3xl font-semibold text-gray-900">{(result.predicted_return * 100).toFixed(3)}%</p>
      <p className="text-xs text-gray-500">This is the model's numeric estimate for the target return, not an actual outcome.</p>
    </div>
  );
}

function ProbabilityBar({ label, value, tone }: { label: string; value: number; tone: 'red' | 'green' }) {
  const percentage = Math.max(0, Math.min(100, value * 100));
  return (
    <div>
      <div className="flex justify-between text-sm">
        <span className="text-gray-700">{label}</span>
        <span className="font-semibold text-gray-900">{percentage.toFixed(1)}%</span>
      </div>
      <div className="mt-1 h-2 rounded-full bg-gray-200" role="img" aria-label={`${label}: ${percentage.toFixed(1)}%`}>
        <div className={`h-2 rounded-full ${tone === 'red' ? 'bg-red-500' : 'bg-green-500'}`} style={{ width: `${percentage}%` }} />
      </div>
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
