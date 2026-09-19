import logging
from typing import Any
import pandas as pd
import numpy as np

from app.repositories.model_repo import ModelRepository
from app.ml.model_trainer import ModelTrainer, Evaluator
from app.services.ml_dataset_service import MLDatasetService

logger = logging.getLogger(__name__)


class EvaluationError(Exception):
    pass


def _safe_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        v = float(value)
        if np.isnan(v) or np.isinf(v):
            return None
        return v
    except (TypeError, ValueError):
        return None


class EvaluationService:
    def __init__(self, db, model_run_id: int, split: str = "test"):
        self.db = db
        self.model_run_id = model_run_id
        self.split = split

    async def evaluate(self) -> dict[str, Any]:
        if self.split not in {"validation", "test"}:
            raise EvaluationError(f"Unsupported split: {self.split}. Supported: validation, test")

        repo = ModelRepository(self.db)
        model_run = await repo.get_by_id(self.model_run_id)
        if not model_run:
            raise EvaluationError(f"Model run {self.model_run_id} not found")

        ml_service = MLDatasetService(self.db)
        splits = await ml_service.get_splits(
            symbol=model_run.symbol,
            start_date=model_run.training_start,
            end_date=model_run.test_end_date or model_run.evaluation_end,
        )

        task_type = model_run.task_type or "classification"
        model_name = model_run.model_name

        if task_type == "classification":
            y_true = splits[f"y_{self.split}_classification"]
            X = splits[f"X_{self.split}"]
        else:
            y_true = splits[f"y_{self.split}_regression"]
            X = splits[f"X_{self.split}"]

        if len(X) == 0:
            raise EvaluationError(f"No {self.split} data available for evaluation")

        trainer = ModelTrainer(
            model_name=model_name,
            task_type=task_type,
            random_state=model_run.random_state or 42,
        )

        X_train = splits["X_train"]
        y_train = splits["y_train_classification"] if task_type == "classification" else splits["y_train_regression"]
        trainer.train(X_train, y_train)

        try:
            y_pred = trainer.predict(X)
        except Exception as exc:
            raise EvaluationError(f"Prediction failed: {exc}") from exc

        if task_type == "classification":
            try:
                y_proba = trainer.predict_proba(X)
            except AttributeError:
                y_proba = None

            metrics = Evaluator.evaluate_classification(y_true, y_pred, y_proba)
            confusion = metrics.get("confusion_matrix", [[0, 0], [0, 0]])
            if isinstance(confusion, list) and len(confusion) == 2 and len(confusion[0]) == 2:
                tn, fp, fn, tp = int(confusion[0][0]), int(confusion[0][1]), int(confusion[1][0]), int(confusion[1][1])
            else:
                tn = fp = fn = tp = 0

            class_dist = self._class_distribution(y_true)
            baseline = self._majority_class_baseline(y_true)

            return {
                "model_run_id": self.model_run_id,
                "model_name": model_name,
                "task_type": task_type,
                "split": self.split,
                "sample_count": len(X),
                "accuracy": _safe_float(metrics.get("accuracy")),
                "precision": _safe_float(metrics.get("precision")),
                "recall": _safe_float(metrics.get("recall")),
                "f1": _safe_float(metrics.get("f1_score")),
                "roc_auc": _safe_float(metrics.get("roc_auc")),
                "confusion_matrix": {
                    "true_negative": tn,
                    "false_positive": fp,
                    "false_negative": fn,
                    "true_positive": tp,
                },
                "class_distribution": class_dist,
                "baseline": baseline,
            }
        else:
            metrics = Evaluator.evaluate_regression(y_true, y_pred)
            baseline = self._mean_baseline(y_true)

            return {
                "model_run_id": self.model_run_id,
                "model_name": model_name,
                "task_type": task_type,
                "split": self.split,
                "sample_count": len(X),
                "mae": _safe_float(metrics.get("mae")),
                "rmse": _safe_float(metrics.get("rmse")),
                "r2": _safe_float(metrics.get("r2")),
                "baseline": baseline,
            }

    @staticmethod
    def _class_distribution(y: pd.Series) -> dict[str, Any]:
        counts = y.value_counts().to_dict()
        total = len(y)
        return {
            "class_0_count": int(counts.get(0, 0)),
            "class_1_count": int(counts.get(1, 0)),
            "class_0_percentage": float(counts.get(0, 0)) / total if total > 0 else 0.0,
            "class_1_percentage": float(counts.get(1, 0)) / total if total > 0 else 0.0,
        }

    @staticmethod
    def _majority_class_baseline(y: pd.Series) -> dict[str, Any]:
        counts = y.value_counts()
        majority_class = int(counts.index[0])
        majority_count = int(counts.iloc[0])
        total = len(y)
        return {
            "strategy": "majority_class",
            "predicted_class": majority_class,
            "accuracy": majority_count / total if total > 0 else 0.0,
            "count": majority_count,
            "total": total,
        }

    @staticmethod
    def _mean_baseline(y: pd.Series) -> dict[str, Any]:
        return {
            "strategy": "training_mean",
            "predicted_value": float(y.mean()) if len(y) > 0 else 0.0,
            "mae": float(np.mean(np.abs(y - y.mean()))) if len(y) > 0 else 0.0,
        }
