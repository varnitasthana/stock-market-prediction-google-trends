import { useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { evaluateModel, fetchMarketDataStatus, fetchModelRuns, trainModel } from '../services/api';
import type { ClassificationEvaluationResponse, MarketDataStatusResponse, ModelRun, RegressionEvaluationResponse } from '../types/api';
import FeatureGlossary from '../components/FeatureGlossary';
import HelpPanel from '../components/HelpPanel';
import PageIntro from '../components/PageIntro';
import StatusBadge from '../components/StatusBadge';
import { formatDisplayDate, getTodayISO } from '../utils/date';

const DEFAULT_SYMBOL = '^NSEI';
const SAFE_START = '2024-01-01';

const CLASSIFICATION_MODELS = [
  { value: 'logistic_regression', label: 'Logistic Regression' },
  { value: 'random_forest_classifier', label: 'Random Forest Classifier' },
];

const REGRESSION_MODELS = [
  { value: 'linear_regression', label: 'Linear Regression' },
  { value: 'random_forest_regressor', label: 'Random Forest Regressor' },
];

const MODEL_FEATURES = [
  'daily_return',
  'log_return',
  'volatility_5d',
  'return_lag_1',
  'return_lag_3',
  'return_lag_5',
  'next_day_return',
  'next_day_direction',
];

type EvaluationResult = ClassificationEvaluationResponse | RegressionEvaluationResponse;

interface EvaluationState {
  modelRunId: number;
  split: string;
  result: EvaluationResult;
}

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

export default function Models() {
  const queryClient = useQueryClient();
  const [task, setTask] = useState('classification');
  const [modelName, setModelName] = useState('logistic_regression');
  const [evaluation, setEvaluation] = useState<EvaluationState | null>(null);
  const [evaluationError, setEvaluationError] = useState<string | null>(null);
  const [evaluationErrorModelId, setEvaluationErrorModelId] = useState<number | null>(null);
  const [evaluationLoadingId, setEvaluationLoadingId] = useState<number | null>(null);

  const { data: marketStatus, isLoading: statusLoading, error: statusError } = useQuery({
    queryKey: ['marketStatus', DEFAULT_SYMBOL],
    queryFn: () => fetchMarketDataStatus(DEFAULT_SYMBOL),
  });

  const rangeStart = marketStatus?.first_stored_date ?? SAFE_START;
  const rangeEnd = marketStatus?.last_stored_date ?? marketStatus?.expected_session ?? getTodayISO();

  const { data: models, isLoading: modelsLoading, error: modelsError } = useQuery({
    queryKey: ['modelRuns'],
    queryFn: () => fetchModelRuns(),
  });

  const trainMutation = useMutation({
    mutationFn: () => trainModel({
      symbol: DEFAULT_SYMBOL,
      start_date: rangeStart,
      end_date: rangeEnd,
      task,
      model_name: modelName,
    }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['modelRuns'] }),
  });

  const handleTaskChange = (event: React.ChangeEvent<HTMLSelectElement>) => {
    const nextTask = event.target.value;
    const nextModels = nextTask === 'classification' ? CLASSIFICATION_MODELS : REGRESSION_MODELS;
    setTask(nextTask);
    setModelName(nextModels[0].value);
  };

  const handleEvaluate = async (modelRunId: number, split: string) => {
    setEvaluationLoadingId(modelRunId);
    setEvaluationError(null);
    try {
      const result = await evaluateModel({ model_run_id: modelRunId, evaluation_split: split });
      setEvaluation({ modelRunId, split, result });
    } catch (error) {
      setEvaluationError(String(error));
      setEvaluationErrorModelId(modelRunId);
    } finally {
      setEvaluationLoadingId(null);
    }
  };

  const availableModels = task === 'classification' ? CLASSIFICATION_MODELS : REGRESSION_MODELS;
  const canTrain = !statusLoading && rangeStart <= rangeEnd;

  return (
    <div className="space-y-6" aria-live="polite">
      <PageIntro
        title="Model Training"
        description="Train and evaluate baseline models on the sessions that are actually stored in the database."
      >
        <StatusOverview status={marketStatus} loading={statusLoading} />
      </PageIntro>

      <HelpPanel title="How to use model training">
        <p><strong>Purpose:</strong> Create a reproducible classification or regression model from historical market and search-interest features.</p>
        <p><strong>Inputs:</strong> The selected task, model algorithm, symbol, and the stored training window. Today and Expected Session describe freshness; Latest Stored Session is the final session available for training.</p>
        <p><strong>Outputs:</strong> A model run with persisted artifacts, feature count, split dates, and evaluation results.</p>
        <p><strong>Interpretation:</strong> Validation and test metrics describe performance on held-out historical sessions. They do not guarantee future returns or directions.</p>
        <p><strong>Limitations:</strong> Small samples, stale data, missing Trends rows, and market regime changes can make metrics unstable.</p>
        <p><strong>Historical patterns:</strong> Compare metrics across model types and splits, then inspect feature definitions and the Statistics page before choosing a model.</p>
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
            <h3 className="text-lg font-semibold text-gray-900">Training Configuration</h3>
            <p className="mt-1 text-sm text-gray-600">The date window follows stored market coverage.</p>
          </div>
          <StatusBadge label={`Training window: ${formatDisplayDate(rangeStart)} to ${formatDisplayDate(rangeEnd)}`} />
        </div>

        <div className="mt-5 grid grid-cols-1 gap-4 sm:grid-cols-3">
          <div>
            <label htmlFor="model-task" className="block text-sm font-medium text-gray-700">Prediction task</label>
            <select
              id="model-task"
              value={task}
              onChange={handleTaskChange}
              className="mt-1 w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
              aria-describedby="model-task-help"
            >
              <option value="classification">Classification: predict Up or Down</option>
              <option value="regression">Regression: predict next-session return</option>
            </select>
            <p id="model-task-help" className="mt-1 text-xs text-gray-500">Classification outputs a direction; regression outputs a numeric return.</p>
          </div>
          <div>
            <label htmlFor="model-name" className="block text-sm font-medium text-gray-700">Model algorithm</label>
            <select
              id="model-name"
              value={modelName}
              onChange={(event) => setModelName(event.target.value)}
              className="mt-1 w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
              aria-describedby="model-name-help"
            >
              {availableModels.map((model) => (
                <option key={model.value} value={model.value}>{model.label}</option>
              ))}
            </select>
            <p id="model-name-help" className="mt-1 text-xs text-gray-500">Choose an algorithm supported for the selected task.</p>
          </div>
          <div className="flex items-end">
            <button
              type="button"
              onClick={() => trainMutation.mutate()}
              disabled={trainMutation.isPending || !canTrain}
              className="w-full rounded-md bg-blue-600 px-4 py-2 text-sm font-semibold text-white hover:bg-blue-500 disabled:cursor-not-allowed disabled:opacity-50"
              aria-describedby="train-model-help"
            >
              {trainMutation.isPending ? 'Training...' : 'Train Model'}
            </button>
          </div>
        </div>
        <p id="train-model-help" className="mt-2 text-xs text-gray-500">
          {statusLoading ? 'Waiting for stored market coverage...' : canTrain ? 'Training uses only rows available in the selected window.' : 'Training is unavailable because the stored date range is invalid.'}
        </p>

        {trainMutation.isSuccess && (
          <p role="status" className="mt-4 rounded-md border border-green-200 bg-green-50 p-3 text-sm text-green-800">
            Training completed. Model run ID: {trainMutation.data?.model_run_id}. The trained model list is refreshing.
          </p>
        )}
        {trainMutation.isError && (
          <p role="alert" className="mt-4 rounded-md border border-red-200 bg-red-50 p-3 text-sm text-red-700">
            Training failed. {String(trainMutation.error)}
          </p>
        )}
      </section>

      <FeatureGlossary
        features={trainMutation.data?.feature_names?.length ? trainMutation.data.feature_names : MODEL_FEATURES}
        title="Model feature guide"
        compact
      />

      <section className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <h3 className="text-lg font-semibold text-gray-900">Trained Models</h3>
            <p className="mt-1 text-sm text-gray-600">Review run dates, targets, artifacts, and held-out evaluation results.</p>
          </div>
          <StatusBadge label={`${models?.length ?? 0} run(s)`} />
        </div>

        {modelsLoading && <p className="mt-4 text-sm text-gray-600">Loading trained models...</p>}
        {modelsError && (
          <p role="alert" className="mt-4 rounded-md border border-red-200 bg-red-50 p-3 text-sm text-red-700">
            Failed to load trained models. {String(modelsError)}
          </p>
        )}
        {!modelsLoading && !modelsError && models?.length === 0 && (
          <p className="mt-4 rounded-md border border-gray-200 bg-gray-50 p-4 text-sm text-gray-600">No trained models are available yet. Configure a task and train a model above.</p>
        )}

        <div className="mt-4 grid grid-cols-1 gap-4 md:grid-cols-2">
          {models?.map((model: ModelRun) => (
            <ModelCard
              key={model.id}
              model={model}
              onEvaluate={handleEvaluate}
              evaluation={evaluation?.modelRunId === model.id ? evaluation : null}
              evaluationLoading={evaluationLoadingId === model.id}
              evaluationError={evaluationErrorModelId === model.id ? evaluationError : null}
            />
          ))}
        </div>
      </section>
    </div>
  );
}

function ModelCard({
  model,
  onEvaluate,
  evaluation,
  evaluationLoading,
  evaluationError,
}: {
  model: ModelRun;
  onEvaluate: (id: number, split: string) => void;
  evaluation: EvaluationState | null;
  evaluationLoading: boolean;
  evaluationError: string | null;
}) {
  return (
    <article className="rounded-lg border border-gray-200 bg-white p-5 shadow-sm">
      <div className="flex items-start justify-between gap-3">
        <div>
          <h3 className="text-lg font-semibold text-gray-900">{model.model_name.split('_').join(' ')}</h3>
          <p className="text-sm text-gray-500">{model.task_type ?? 'Unknown task'} · {model.symbol}</p>
        </div>
        <StatusBadge label={`Run #${model.id}`} />
      </div>

      <div className="mt-4 grid grid-cols-1 gap-3 text-sm sm:grid-cols-2">
        <Info label="Target" value={model.target_name?.split('_').join(' ') ?? 'N/A'} />
        <Info label="Feature count" value={model.feature_count?.toString() ?? 'N/A'} />
        <Info label="Training sessions" value={`${formatDisplayDate(model.training_start)} to ${formatDisplayDate(model.training_end)}`} />
        <Info label="Validation sessions" value={`${formatDisplayDate(model.evaluation_start)} to ${formatDisplayDate(model.evaluation_end)}`} />
        {model.test_start_date && model.test_end_date ? (
          <Info label="Test sessions" value={`${formatDisplayDate(model.test_start_date)} to ${formatDisplayDate(model.test_end_date)}`} />
        ) : (
          <Info label="Test sessions" value="Not recorded" />
        )}
        <Info label="Artifact" value={model.artifact_path ? 'Persisted' : 'Missing'} />
      </div>

      <div className="mt-4 flex flex-wrap gap-2">
        <button
          type="button"
          onClick={() => onEvaluate(model.id, 'validation')}
          disabled={evaluationLoading}
          className="rounded-md border border-gray-300 px-3 py-1.5 text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:cursor-not-allowed disabled:opacity-50"
          aria-label={`Evaluate validation split for ${model.model_name} run ${model.id}`}
        >
          {evaluationLoading ? 'Evaluating...' : 'Evaluate Validation'}
        </button>
        <button
          type="button"
          onClick={() => onEvaluate(model.id, 'test')}
          disabled={evaluationLoading}
          className="rounded-md border border-gray-300 px-3 py-1.5 text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:cursor-not-allowed disabled:opacity-50"
          aria-label={`Evaluate test split for ${model.model_name} run ${model.id}`}
        >
          {evaluationLoading ? 'Evaluating...' : 'Evaluate Test'}
        </button>
      </div>

      {evaluation && (
        <div role="status" className="mt-4 rounded-md border border-gray-200 bg-gray-50 p-4">
          <h4 className="text-sm font-semibold text-gray-900">Evaluation: {evaluation.split}</h4>
          <EvaluationMetrics result={evaluation.result} />
        </div>
      )}
      {evaluationError && evaluationLoading === false && (
        <p role="alert" className="mt-4 text-sm text-red-700">Evaluation failed. {evaluationError}</p>
      )}
    </article>
  );
}

function EvaluationMetrics({ result }: { result: EvaluationResult }) {
  if (result.task_type === 'classification') {
    const classification = result as ClassificationEvaluationResponse;
    return (
      <div className="mt-3 grid grid-cols-2 gap-3 text-sm">
        <Info label="Accuracy" value={formatMetric(classification.accuracy)} />
        <Info label="F1 score" value={formatMetric(classification.f1)} />
        <Info label="Precision" value={formatMetric(classification.precision)} />
        <Info label="Recall" value={formatMetric(classification.recall)} />
        <Info label="ROC AUC" value={formatMetric(classification.roc_auc)} />
        <Info label="Sample count" value={String(classification.sample_count)} />
      </div>
    );
  }

  const regression = result as RegressionEvaluationResponse;
  return (
    <div className="mt-3 grid grid-cols-2 gap-3 text-sm">
      <Info label="MAE" value={formatMetric(regression.mae)} />
      <Info label="RMSE" value={formatMetric(regression.rmse)} />
      <Info label="R-squared" value={formatMetric(regression.r2)} />
      <Info label="Sample count" value={String(regression.sample_count)} />
    </div>
  );
}

function formatMetric(value: number | null | undefined): string {
  return value == null ? 'N/A' : value.toFixed(4);
}

function Info({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <p className="text-xs text-gray-500">{label}</p>
      <p className="text-sm font-medium text-gray-900">{value}</p>
    </div>
  );
}
