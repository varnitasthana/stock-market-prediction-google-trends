import logging
from datetime import date
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd

from app.ml.model_trainer import (
    SUPPORTED_TASKS,
    ModelTrainer,
)
from app.repositories.model_repo import ModelRepository
from app.schemas.models import ModelRunCreate

logger = logging.getLogger(__name__)

ARTIFACTS_DIR = Path(__file__).resolve().parent.parent.parent / "artifacts" / "models"
ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)


class TrainingError(Exception):
    pass


class TrainingService:
    def __init__(self, db, symbol: str, start_date: date, end_date: date, task_type: str, model_name: str, random_state: int = 42):
        if task_type not in SUPPORTED_TASKS:
            raise TrainingError(f"Unsupported task type: {task_type}. Supported: {SUPPORTED_TASKS}")
        self.db = db
        self.symbol = symbol
        self.start_date = start_date
        self.end_date = end_date
        self.task_type = task_type
        self.model_name = model_name
        self.random_state = random_state
        self.repo = ModelRepository(db)

    async def train(self) -> dict[str, Any]:
        from app.services.ml_dataset_service import MLDatasetService

        ml_service = MLDatasetService(self.db)
        splits = await ml_service.get_splits(self.symbol, self.start_date, self.end_date)

        feature_columns = splits["feature_names"]
        target_name = "next_day_direction" if self.task_type == "classification" else "next_day_return"

        if target_name in feature_columns:
            raise TrainingError(f"Target column '{target_name}' must not be in feature columns")

        X_train = splits["X_train"]
        y_train = splits[f"y_train_{'classification' if self.task_type == 'classification' else 'regression'}"]
        X_validation = splits["X_validation"]
        y_validation = splits[f"y_validation_{'classification' if self.task_type == 'classification' else 'regression'}"]
        X_test = splits["X_test"]
        y_test = splits[f"y_test_{'classification' if self.task_type == 'classification' else 'regression'}"]

        if self.task_type == "classification":
            self._validate_classification_target(y_train, "training")
            self._validate_classification_target(y_validation, "validation")
            self._validate_classification_target(y_test, "test")
        else:
            self._validate_regression_target(y_train, "training")
            self._validate_regression_target(y_validation, "validation")
            self._validate_regression_target(y_test, "test")

        if len(X_train) < 2:
            raise TrainingError(f"Insufficient training observations: {len(X_train)}")

        trainer = ModelTrainer(
            model_name=self.model_name,
            task_type=self.task_type,
            random_state=self.random_state,
        )
        trainer.train(X_train, y_train)

        train_predictions = trainer.predict(X_train)
        validation_predictions = trainer.predict(X_validation)
        test_predictions = trainer.predict(X_test)

        parameters: dict[str, Any] = {}
        if self.task_type == "classification" and self.model_name == "logistic_regression":
            parameters = {
                "max_iter": 1000,
                "random_state": self.random_state,
                "scaler": "StandardScaler",
            }
        elif self.task_type == "classification" and self.model_name == "random_forest_classifier":
            parameters = {
                "n_estimators": 100,
                "random_state": self.random_state,
            }
        elif self.task_type == "regression" and self.model_name == "linear_regression":
            parameters = {
                "scaler": "StandardScaler",
            }
        elif self.task_type == "regression" and self.model_name == "random_forest_regressor":
            parameters = {
                "n_estimators": 100,
                "random_state": self.random_state,
            }
        elif self.model_name in {"lstm_classifier", "lstm_regressor", "transformer_classifier", "transformer_regressor"}:
            parameters = {
                "architecture": self.model_name,
                "random_state": self.random_state,
            }

        model_run = await self.repo.create(
            ModelRunCreate(
                model_name=self.model_name,
                symbol=self.symbol,
                task_type=self.task_type,
                target_name=target_name,
                training_start=splits["train_start_date"],
                training_end=splits["train_end_date"],
                evaluation_start=splits["validation_start_date"],
                evaluation_end=splits["validation_end_date"],
                test_start_date=splits["test_start_date"],
                test_end_date=splits["test_end_date"],
                metrics=None,
            )
        )

        artifact_path = ARTIFACTS_DIR / f"model_run_{model_run.id}.joblib"
        artifact = {
            "model": trainer.model,
            "model_name": self.model_name,
            "task_type": self.task_type,
            "feature_columns": feature_columns,
            "target_name": target_name,
            "random_state": self.random_state,
            "parameters": parameters,
        }

        if self.model_name not in {"lstm_classifier", "lstm_regressor", "transformer_classifier", "transformer_regressor"}:
            try:
                import shap
                import warnings
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore")
                    if (self.task_type == "classification" and hasattr(trainer.model, "predict_proba")) or self.task_type == "regression":
                        explainer = shap.Explainer(trainer.model, X_train)
                    else:
                        explainer = None
                if explainer is not None:
                    artifact["shap_explainer"] = explainer
            except Exception as exc:
                logger.warning("Could not create SHAP explainer: %s", exc)

        joblib.dump(artifact, artifact_path)
        await self.repo.update_artifact_path(model_run.id, str(artifact_path))
        model_run.artifact_path = str(artifact_path)

        try:
            import mlflow
            import mlflow.sklearn
            from app.core.config import get_settings
            settings = get_settings()
            if hasattr(settings, "mlflow_tracking_uri") and settings.mlflow_tracking_uri:
                mlflow.set_tracking_uri(settings.mlflow_tracking_uri)
                mlflow.set_experiment(f"{self.symbol}_{self.task_type}")
                with mlflow.start_run(run_name=f"{self.model_name}_{model_run.id}"):
                    mlflow.log_params(parameters)
                    if self.task_type == "classification":
                        from app.ml.model_trainer import Evaluator
                        train_preds = trainer.predict(X_train)
                        train_metrics = Evaluator.evaluate_classification(y_train, train_preds)
                        mlflow.log_metrics({f"train_{k}": v for k, v in train_metrics.items() if isinstance(v, (int, float))})
                    else:
                        from app.ml.model_trainer import Evaluator
                        train_preds = trainer.predict(X_train)
                        train_metrics = Evaluator.evaluate_regression(y_train, train_preds)
                        mlflow.log_metrics({f"train_{k}": v for k, v in train_metrics.items() if isinstance(v, (int, float))})
                    if self.model_name not in {"lstm_classifier", "lstm_regressor", "transformer_classifier", "transformer_regressor"}:
                        try:
                            mlflow.sklearn.log_model(trainer.model, "model")
                        except Exception as exc:
                            logger.warning("Could not log model to MLflow: %s", exc)
        except Exception as exc:
            logger.warning("MLflow logging failed: %s", exc)

        return {
            "model_run_id": model_run.id,
            "model_name": self.model_name,
            "task_type": self.task_type,
            "symbol": self.symbol,
            "target_name": target_name,
            "feature_names": feature_columns,
            "feature_count": len(feature_columns),
            "parameters": parameters,
            "random_state": self.random_state,
            "training_rows": len(X_train),
            "validation_rows": len(X_validation),
            "test_rows": len(X_test),
            "training_start_date": splits["train_start_date"],
            "training_end_date": splits["train_end_date"],
            "validation_start_date": splits["validation_start_date"],
            "validation_end_date": splits["validation_end_date"],
            "test_start_date": splits["test_start_date"],
            "test_end_date": splits["test_end_date"],
            "training_completed": True,
            "train_prediction_shape": list(train_predictions.shape),
            "validation_prediction_shape": list(validation_predictions.shape),
            "test_prediction_shape": list(test_predictions.shape),
            "artifact_path": str(artifact_path),
        }

    @staticmethod
    def _validate_classification_target(y: pd.Series, split_name: str):
        unique = set(y.dropna().unique())
        if not unique.issubset({0, 1}):
            raise TrainingError(f"Classification target in {split_name} contains invalid values: {unique - {0, 1}}")

    @staticmethod
    def _validate_regression_target(y: pd.Series, split_name: str):
        if y.isna().any():
            raise TrainingError(f"Regression target in {split_name} contains NaN values")
        if np.isinf(y).any():
            raise TrainingError(f"Regression target in {split_name} contains infinite values")
