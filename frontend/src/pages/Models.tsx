import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { fetchModelRuns, trainModel, evaluateModel } from '../services/api';
import type { ModelRun, ClassificationEvaluationResponse, RegressionEvaluationResponse } from '../types/api';
import { useState } from 'react';

const DEFAULT_SYMBOL = '^NSEI';
const DEFAULT_START = '2024-01-01';
const DEFAULT_END = '2024-06-30';

const CLASSIFICATION_MODELS = [
  { value: 'logistic_regression', label: 'Logistic Regression' },
  { value: 'random_forest_classifier', label: 'Random Forest Classifier' },
];

const REGRESSION_MODELS = [
  { value: 'linear_regression', label: 'Linear Regression' },
  { value: 'random_forest_regressor', label: 'Random Forest Regressor' },
];

export default function Models() {
  const queryClient = useQueryClient();
  const [task, setTask] = useState('classification');
  const [modelName, setModelName] = useState('logistic_regression');

  const { data: models, isLoading: modelsLoading, error: modelsError } = useQuery({
    queryKey: ['modelRuns'],
    queryFn: () => fetchModelRuns(),
  });

  const trainMutation = useMutation({
    mutationFn: trainModel,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['modelRuns'] }),
  });

  const handleTrain = () => {
    trainMutation.mutate({
      symbol: DEFAULT_SYMBOL,
      start_date: DEFAULT_START,
      end_date: DEFAULT_END,
      task,
      model_name: modelName,
    });
  };

  const handleEvaluate = async (modelRunId: number, split: string) => {
    const result = await evaluateModel({ model_run_id: modelRunId, evaluation_split: split });
    alert(JSON.stringify(result, null, 2));
  };

  return (
    <div className="space-y-6">
      <section>
        <h2 className="text-xl font-semibold text-gray-900">Model Training</h2>
        <p className="mt-1 text-sm text-gray-500">Train baseline models using the canonical Phase 8 dataset</p>
        <div className="mt-4 grid grid-cols-1 gap-4 sm:grid-cols-3">
          <div>
            <label className="block text-sm font-medium text-gray-700">Task</label>
            <select value={task} onChange={(e) => setTask(e.target.value)} className="mt-1 rounded-md border border-gray-300 px-3 py-2 text-sm">
              <option value="classification">Classification</option>
              <option value="regression">Regression</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700">Model</label>
            <select value={modelName} onChange={(e) => setModelName(e.target.value)} className="mt-1 rounded-md border border-gray-300 px-3 py-2 text-sm">
              {(task === 'classification' ? CLASSIFICATION_MODELS : REGRESSION_MODELS).map((m) => (
                <option key={m.value} value={m.value}>{m.label}</option>
              ))}
            </select>
          </div>
          <div className="flex items-end">
            <button onClick={handleTrain} disabled={trainMutation.isPending} className="rounded-md bg-blue-600 px-4 py-2 text-sm font-semibold text-white hover:bg-blue-500 disabled:opacity-50">
              {trainMutation.isPending ? 'Training...' : 'Train Model'}
            </button>
          </div>
        </div>
        {trainMutation.isSuccess && (
          <p className="mt-2 text-sm text-green-700">Training completed. Model run ID: {trainMutation.data?.model_run_id}</p>
        )}
        {trainMutation.isError && (
          <p className="mt-2 text-sm text-red-600">Training failed.</p>
        )}
      </section>

      <section>
        <h2 className="text-xl font-semibold text-gray-900">Trained Models</h2>
        <p className="mt-1 text-sm text-gray-500">Phase 9 training results and Phase 10 evaluation</p>
        {modelsLoading && <p className="mt-2 text-sm text-gray-600">Loading models...</p>}
        {modelsError && <p className="mt-2 text-sm text-red-600">Failed to load models.</p>}
        {!modelsLoading && !modelsError && models && models.length === 0 && (
          <p className="mt-2 text-sm text-gray-600">No trained models yet. Train a model above.</p>
        )}
        <div className="mt-4 grid grid-cols-1 gap-4 md:grid-cols-2">
          {models?.map((model: ModelRun) => (
            <ModelCard key={model.id} model={model} onEvaluate={handleEvaluate} />
          ))}
        </div>
      </section>
    </div>
  );
}

function ModelCard({ model, onEvaluate }: { model: ModelRun; onEvaluate: (id: number, split: string) => void }) {
  return (
    <div className="rounded-lg border border-gray-200 bg-white p-5 shadow-sm">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-lg font-semibold text-gray-900">{model.model_name}</h3>
          <p className="text-sm text-gray-500">{model.task_type} · {model.symbol}</p>
        </div>
        <span className="rounded-full bg-gray-100 px-3 py-1 text-xs font-medium text-gray-700">Run #{model.id}</span>
      </div>
      <div className="mt-4 grid grid-cols-2 gap-3 text-sm">
        <Info label="Target" value={model.target_name ?? 'N/A'} />
        <Info label="Features" value={String(model.feature_count ?? 'N/A')} />
        <Info label="Train" value={`${model.training_start} → ${model.training_end}`} />
        <Info label="Validation" value={`${model.evaluation_start} → ${model.evaluation_end}`} />
        {model.test_start_date && model.test_end_date && (
          <Info label="Test" value={`${model.test_start_date} → ${model.test_end_date}`} />
        )}
        <Info label="Artifact" value={model.artifact_path ? 'Persisted' : 'Missing'} />
      </div>
      <div className="mt-4 flex gap-2">
        <button onClick={() => onEvaluate(model.id, 'validation')} className="rounded-md border border-gray-300 px-3 py-1.5 text-sm font-medium text-gray-700 hover:bg-gray-50">
          Evaluate Validation
        </button>
        <button onClick={() => onEvaluate(model.id, 'test')} className="rounded-md border border-gray-300 px-3 py-1.5 text-sm font-medium text-gray-700 hover:bg-gray-50">
          Evaluate Test
        </button>
      </div>
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
