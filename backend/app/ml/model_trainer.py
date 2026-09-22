import logging
from typing import Any

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LinearRegression, LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

logger = logging.getLogger(__name__)


class ModelTrainingError(Exception):
    """Raised when model training fails"""


class ModelPredictionError(Exception):
    """Raised when model prediction fails"""


def _is_tensorflow_available() -> bool:
    try:
        import tensorflow as tf  # noqa: F401
        return True
    except ImportError:
        return False


_TENSORFLOW_AVAILABLE = _is_tensorflow_available()

if _TENSORFLOW_AVAILABLE:
    SUPPORTED_CLASSIFICATION_MODELS = {
        "logistic_regression",
        "random_forest_classifier",
        "lstm_classifier",
        "transformer_classifier",
    }
    SUPPORTED_REGRESSION_MODELS = {
        "linear_regression",
        "random_forest_regressor",
        "lstm_regressor",
        "transformer_regressor",
    }
else:
    SUPPORTED_CLASSIFICATION_MODELS = {
        "logistic_regression",
        "random_forest_classifier",
    }
    SUPPORTED_REGRESSION_MODELS = {
        "linear_regression",
        "random_forest_regressor",
    }

SUPPORTED_TASKS = {"classification", "regression"}


class ModelTrainer:
    def __init__(self, model_name: str, task_type: str, random_state: int = 42):
        if task_type not in SUPPORTED_TASKS:
            raise ValueError(f"Unsupported task type: {task_type}. Supported: {SUPPORTED_TASKS}")
        self.model_name = model_name
        self.task_type = task_type
        self.random_state = random_state
        self.model = self._build_model()
        self.feature_columns: list[str] = []

    def _build_model(self):
        if self.task_type == "classification":
            return self._build_classification_model()
        elif self.task_type == "regression":
            return self._build_regression_model()
        else:
            raise ValueError(f"Unsupported task type: {self.task_type}")

    def _build_classification_model(self):
        if self.model_name == "logistic_regression":
            return Pipeline([
                ("imputer", SimpleImputer(strategy="mean")),
                ("scaler", StandardScaler()),
                ("clf", LogisticRegression(max_iter=1000, random_state=self.random_state)),
            ])
        elif self.model_name == "random_forest_classifier":
            return RandomForestClassifier(n_estimators=100, random_state=self.random_state, n_jobs=-1)
        elif self.model_name == "lstm_classifier":
            try:
                import tensorflow as tf
                from tensorflow import keras
                tf.random.set_seed(self.random_state)
                model = keras.Sequential([
                    keras.layers.LSTM(64, return_sequences=False, input_shape=(None, 1)),
                    keras.layers.Dropout(0.2),
                    keras.layers.Dense(1, activation="sigmoid"),
                ])
                model.compile(optimizer="adam", loss="binary_crossentropy", metrics=["accuracy"])
                return model
            except ImportError as exc:
                raise ValueError("TensorFlow is required for LSTM models. Install it with: pip install tensorflow") from exc
        elif self.model_name == "transformer_classifier":
            try:
                import tensorflow as tf
                from tensorflow import keras
                tf.random.set_seed(self.random_state)
                inputs = keras.layers.Input(shape=(None, 1))
                x = keras.layers.MultiHeadAttention(num_heads=4, key_dim=32)(inputs, inputs)
                x = keras.layers.GlobalAveragePooling1D()(x)
                x = keras.layers.Dense(64, activation="relu")(x)
                x = keras.layers.Dropout(0.2)(x)
                outputs = keras.layers.Dense(1, activation="sigmoid")(x)
                model = keras.Model(inputs=inputs, outputs=outputs)
                model.compile(optimizer="adam", loss="binary_crossentropy", metrics=["accuracy"])
                return model
            except ImportError as exc:
                raise ValueError("TensorFlow is required for Transformer models. Install it with: pip install tensorflow") from exc
        else:
            raise ValueError(f"Unsupported classification model: {self.model_name}")

    def _build_regression_model(self):
        if self.model_name == "linear_regression":
            return Pipeline([
                ("imputer", SimpleImputer(strategy="mean")),
                ("scaler", StandardScaler()),
                ("reg", LinearRegression()),
            ])
        elif self.model_name == "random_forest_regressor":
            return RandomForestRegressor(n_estimators=100, random_state=self.random_state, n_jobs=-1)
        elif self.model_name == "lstm_regressor":
            try:
                import tensorflow as tf
                from tensorflow import keras
                tf.random.set_seed(self.random_state)
                model = keras.Sequential([
                    keras.layers.LSTM(64, return_sequences=False, input_shape=(None, 1)),
                    keras.layers.Dropout(0.2),
                    keras.layers.Dense(1),
                ])
                model.compile(optimizer="adam", loss="mse", metrics=["mae"])
                return model
            except ImportError as exc:
                raise ValueError("TensorFlow is required for LSTM models. Install it with: pip install tensorflow") from exc
        elif self.model_name == "transformer_regressor":
            try:
                import tensorflow as tf
                from tensorflow import keras
                tf.random.set_seed(self.random_state)
                inputs = keras.layers.Input(shape=(None, 1))
                x = keras.layers.MultiHeadAttention(num_heads=4, key_dim=32)(inputs, inputs)
                x = keras.layers.GlobalAveragePooling1D()(x)
                x = keras.layers.Dense(64, activation="relu")(x)
                x = keras.layers.Dropout(0.2)(x)
                outputs = keras.layers.Dense(1)(x)
                model = keras.Model(inputs=inputs, outputs=outputs)
                model.compile(optimizer="adam", loss="mse", metrics=["mae"])
                return model
            except ImportError as exc:
                raise ValueError("TensorFlow is required for Transformer models. Install it with: pip install tensorflow") from exc
        else:
            raise ValueError(f"Unsupported regression model: {self.model_name}")

    def train(self, X: pd.DataFrame, y: pd.Series):
        # Input validation
        if X.empty:
            raise ValueError("Training data (X) cannot be empty")
        if len(y) == 0:
            raise ValueError("Training labels (y) cannot be empty")
        if len(X) != len(y):
            raise ValueError(f"Feature matrix length ({len(X)}) does not match label length ({len(y)})")
        if X.isna().all().any():
            raise ValueError("Training data contains columns with all NaN values")
        
        self.feature_columns = list(X.columns)
        
        if self.model_name in {"lstm_classifier", "lstm_regressor", "transformer_classifier", "transformer_regressor"}:
            X_arr = np.expand_dims(X.values, axis=-1)
            if hasattr(self.model, "fit"):
                self.model.fit(X_arr, y, epochs=20, batch_size=min(16, len(X)), verbose=0)
            else:
                raise ValueError(f"Model {self.model_name} does not support fit")
        else:
            self.model.fit(X, y)
        logger.info("Trained %s (%s) on %d samples", self.model_name, self.task_type, len(X))

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        # Input validation
        if X.empty:
            raise ValueError("Prediction data (X) cannot be empty")
        if not self.feature_columns:
            raise ValueError("Model has not been trained yet (feature_columns is empty)")
        
        missing_cols = set(self.feature_columns) - set(X.columns)
        if missing_cols:
            raise ValueError(f"Missing required features: {missing_cols}")
        
        # Ensure column order matches training
        X = X[self.feature_columns]
        
        if self.model_name in {"lstm_classifier", "lstm_regressor", "transformer_classifier", "transformer_regressor"}:
            X_arr = np.expand_dims(X.values, axis=-1)
            preds = self.model.predict(X_arr, verbose=0)
            if self.task_type == "classification":
                return (preds > 0.5).astype(int).flatten()
            return preds.flatten()
        return self.model.predict(X)

    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        if self.model_name in {"lstm_classifier", "transformer_classifier"}:
            X_arr = np.expand_dims(X.values, axis=-1)
            preds = self.model.predict(X_arr, verbose=0).flatten()
            return np.column_stack([1 - preds, preds])
        if not hasattr(self.model, "predict_proba"):
            raise AttributeError(f"{self.model_name} does not support predict_proba")
        return self.model.predict_proba(X)

    def get_feature_importance(self) -> dict[str, float]:
        if self.model_name in {"lstm_classifier", "lstm_regressor", "transformer_classifier", "transformer_regressor"}:
            return {}
        if hasattr(self.model, "feature_importances_"):
            return dict(zip(self.feature_columns, self.model.feature_importances_, strict=True))
        if hasattr(self.model, "named_steps") and hasattr(self.model.named_steps.get("clf", None), "feature_importances_"):
            clf = self.model.named_steps["clf"]
            return dict(zip(self.feature_columns, clf.feature_importances_, strict=True))
        if hasattr(self.model, "named_steps") and hasattr(self.model.named_steps.get("reg", None), "feature_importances_"):
            reg = self.model.named_steps["reg"]
            return dict(zip(self.feature_columns, reg.feature_importances_, strict=True))
        return {}


class Evaluator:
    @staticmethod
    def evaluate_classification(y_true: pd.Series, y_pred: np.ndarray, y_proba: np.ndarray | None = None) -> dict[str, Any]:
        from sklearn.metrics import (
            accuracy_score,
            confusion_matrix,
            f1_score,
            precision_score,
            recall_score,
        )
        metrics = {
            "accuracy": float(accuracy_score(y_true, y_pred)),
            "precision": float(precision_score(y_true, y_pred, zero_division=0)),
            "recall": float(recall_score(y_true, y_pred, zero_division=0)),
            "f1_score": float(f1_score(y_true, y_pred, zero_division=0)),
            "confusion_matrix": confusion_matrix(y_true, y_pred).tolist(),
        }
        if y_proba is not None and y_proba.shape[1] == 2:
            try:
                from sklearn.metrics import roc_auc_score
                metrics["roc_auc"] = float(roc_auc_score(y_true, y_proba[:, 1]))
            except Exception as exc:
                logger.warning("Could not compute ROC-AUC: %s", exc)
        return metrics

    @staticmethod
    def evaluate_regression(y_true: pd.Series, y_pred: np.ndarray) -> dict[str, Any]:
        from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
        mse = mean_squared_error(y_true, y_pred)
        return {
            "mae": float(mean_absolute_error(y_true, y_pred)),
            "rmse": float(np.sqrt(mse)),
            "r2": float(r2_score(y_true, y_pred)),
        }
