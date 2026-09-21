import logging
from datetime import date
from pathlib import Path
from typing import Any

import joblib
import pandas as pd

from app.repositories.features_repo import FeaturesRepository
from app.repositories.model_repo import ModelRepository
from app.repositories.prediction_repo import PredictionRepository
from app.services.ml_dataset_service import MLDatasetService

logger = logging.getLogger(__name__)


class PredictionError(Exception):
    pass


class PredictionService:
    def __init__(self, db, model_run_id: int, symbol: str, prediction_date: date):
        self.db = db
        self.model_run_id = model_run_id
        self.symbol = symbol
        self.prediction_date = prediction_date
        self.model_repo = ModelRepository(db)
        self.features_repo = FeaturesRepository(db)
        self.prediction_repo = PredictionRepository(db)

    async def predict(self) -> dict[str, Any]:
        model_run = await self.model_repo.get_by_id(self.model_run_id)
        if not model_run:
            raise PredictionError(f"Model run {self.model_run_id} not found")

        if model_run.symbol != self.symbol:
            raise PredictionError(
                f"Symbol mismatch: model was trained on {model_run.symbol}, but prediction requested for {self.symbol}"
            )

        artifact_path = model_run.artifact_path
        if not artifact_path:
            raise PredictionError(f"Model run {self.model_run_id} does not have a persisted artifact")

        path = Path(artifact_path)
        if not path.exists():
            raise PredictionError(f"Model artifact not found at {artifact_path}")

        try:
            artifact = joblib.load(path)
        except Exception as exc:
            raise PredictionError(f"Failed to load model artifact: {exc}") from exc

        model = artifact.get("model")
        feature_columns = artifact.get("feature_columns")
        task_type = artifact.get("task_type")
        model_name = artifact.get("model_name")
        target_name = artifact.get("target_name")
        shap_explainer = artifact.get("shap_explainer")

        if model is None:
            raise PredictionError("Model artifact does not contain a model")
        if not feature_columns:
            raise PredictionError("Model artifact does not contain feature columns")

        ml_service = MLDatasetService(self.db)
        rows = await self.features_repo.get_by_symbol_and_date_range(
            self.symbol,
            self.prediction_date,
            self.prediction_date,
        )
        if not rows:
            raise PredictionError(
                f"No engineered features found for {self.symbol} on {self.prediction_date}"
            )

        wide_df = ml_service._pivot_to_wide(rows)
        if wide_df.empty:
            raise PredictionError(
                f"No feature data available for {self.symbol} on {self.prediction_date}"
            )

        missing_features = [c for c in feature_columns if c not in wide_df.columns]
        if missing_features:
            raise PredictionError(f"Missing features for prediction: {missing_features}")

        feature_row = wide_df.loc[wide_df["date"] == pd.to_datetime(self.prediction_date), feature_columns]
        if feature_row.empty:
            raise PredictionError(
                f"Feature row not found for {self.symbol} on {self.prediction_date}"
            )

        X = feature_row[feature_columns].reset_index(drop=True)
        if X.isna().any().any():
            raise PredictionError("Feature row contains missing values; prediction cannot proceed")

        try:
            y_pred = model.predict(X)
        except Exception as exc:
            raise PredictionError(f"Prediction failed: {exc}") from exc

        predicted_value = float(y_pred[0])

        if task_type == "classification":
            proba = None
            if hasattr(model, "predict_proba"):
                try:
                    proba = model.predict_proba(X)[0]
                except Exception:
                    proba = None

            shap_values = None
            if shap_explainer is not None:
                try:
                    if model_name in {"lstm_classifier", "transformer_classifier"}:
                        X_arr = pd.DataFrame({c: X[c] for c in feature_columns}).values
                        X_arr = X_arr.reshape(1, X_arr.shape[0], 1)
                        shap_values = shap_explainer(X_arr).values
                    else:
                        shap_values = shap_explainer(X).values
                except Exception as exc:
                    logger.warning("SHAP computation failed: %s", exc)

            return {
                "model_run_id": self.model_run_id,
                "model_name": model_name,
                "task_type": task_type,
                "symbol": self.symbol,
                "prediction_date": self.prediction_date,
                "target_name": target_name,
                "predicted_class": int(predicted_value),
                "predicted_direction": "Up" if int(predicted_value) == 1 else "Down",
                "probability_down": float(proba[0]) if proba is not None else None,
                "probability_up": float(proba[1]) if proba is not None else None,
                "shap_values": shap_values.tolist() if shap_values is not None else None,
                "feature_columns": feature_columns,
            }
        else:
            shap_values = None
            if shap_explainer is not None:
                try:
                    if model_name in {"lstm_regressor", "transformer_regressor"}:
                        X_arr = pd.DataFrame({c: X[c] for c in feature_columns}).values
                        X_arr = X_arr.reshape(1, X_arr.shape[0], 1)
                        shap_values = shap_explainer(X_arr).values
                    else:
                        shap_values = shap_explainer(X).values
                except Exception as exc:
                    logger.warning("SHAP computation failed: %s", exc)

            return {
                "model_run_id": self.model_run_id,
                "model_name": model_name,
                "task_type": task_type,
                "symbol": self.symbol,
                "prediction_date": self.prediction_date,
                "target_name": target_name,
                "predicted_return": predicted_value,
                "shap_values": shap_values.tolist() if shap_values is not None else None,
                "feature_columns": feature_columns,
            }

    async def get_predictions_by_model_run(self, model_run_id: int):
        return await self.prediction_repo.get_by_model_run(model_run_id)

    async def get_latest_predictions(self, symbol: str):
        return await self.prediction_repo.get_latest(symbol)
