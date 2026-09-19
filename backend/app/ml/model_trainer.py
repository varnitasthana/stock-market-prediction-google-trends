import logging
from typing import Dict, Any, List, Tuple
import pandas as pd
import numpy as np
from sklearn.linear_model import LogisticRegression, LinearRegression
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline

logger = logging.getLogger(__name__)

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
                ("scaler", StandardScaler()),
                ("clf", LogisticRegression(max_iter=1000, random_state=self.random_state)),
            ])
        elif self.model_name == "random_forest_classifier":
            return RandomForestClassifier(n_estimators=100, random_state=self.random_state, n_jobs=-1)
        else:
            raise ValueError(f"Unsupported classification model: {self.model_name}")

    def _build_regression_model(self):
        if self.model_name == "linear_regression":
            return Pipeline([
                ("scaler", StandardScaler()),
                ("reg", LinearRegression()),
            ])
        elif self.model_name == "random_forest_regressor":
            return RandomForestRegressor(n_estimators=100, random_state=self.random_state, n_jobs=-1)
        else:
            raise ValueError(f"Unsupported regression model: {self.model_name}")

    def train(self, X: pd.DataFrame, y: pd.Series):
        self.feature_columns = list(X.columns)
        self.model.fit(X, y)
        logger.info("Trained %s (%s) on %d samples", self.model_name, self.task_type, len(X))

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        return self.model.predict(X)

    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        if not hasattr(self.model, "predict_proba"):
            raise AttributeError(f"{self.model_name} does not support predict_proba")
        return self.model.predict_proba(X)

    def get_feature_importance(self) -> Dict[str, float]:
        if hasattr(self.model, "feature_importances_"):
            return dict(zip(self.feature_columns, self.model.feature_importances_))
        if hasattr(self.model, "named_steps") and hasattr(self.model.named_steps.get("clf", None), "feature_importances_"):
            clf = self.model.named_steps["clf"]
            return dict(zip(self.feature_columns, clf.feature_importances_))
        if hasattr(self.model, "named_steps") and hasattr(self.model.named_steps.get("reg", None), "feature_importances_"):
            reg = self.model.named_steps["reg"]
            return dict(zip(self.feature_columns, reg.feature_importances_))
        return {}


class Evaluator:
    @staticmethod
    def evaluate_classification(y_true: pd.Series, y_pred: np.ndarray, y_proba: np.ndarray | None = None) -> Dict[str, Any]:
        from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix
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
    def evaluate_regression(y_true: pd.Series, y_pred: np.ndarray) -> Dict[str, Any]:
        from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
        mse = mean_squared_error(y_true, y_pred)
        return {
            "mae": float(mean_absolute_error(y_true, y_pred)),
            "rmse": float(np.sqrt(mse)),
            "r2": float(r2_score(y_true, y_pred)),
        }
