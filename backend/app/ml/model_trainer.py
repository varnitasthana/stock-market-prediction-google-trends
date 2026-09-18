import logging
from typing import Dict, Any, Tuple, Optional
import pandas as pd
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score, confusion_matrix
import xgboost as xgb

logger = logging.getLogger(__name__)


class ModelTrainer:
    def __init__(self, model_type: str = "logistic_regression"):
        self.model_type = model_type
        self.model = None
        self.feature_columns: list[str] = []
        self.scaler = StandardScaler()

    def _build_model(self):
        if self.model_type == "logistic_regression":
            return Pipeline([
                ("scaler", StandardScaler()),
                ("clf", LogisticRegression(max_iter=1000, random_state=42)),
            ])
        elif self.model_type == "random_forest":
            return RandomForestClassifier(n_estimators=200, max_depth=10, min_samples_split=5, random_state=42, n_jobs=-1)
        elif self.model_type == "gradient_boosting":
            return GradientBoostingClassifier(n_estimators=200, max_depth=4, learning_rate=0.05, random_state=42)
        elif self.model_type == "xgboost":
            return xgb.XGBClassifier(n_estimators=200, max_depth=4, learning_rate=0.05, random_state=42, n_jobs=-1)
        else:
            raise ValueError(f"Unknown model type: {self.model_type}")

    def train(self, X: pd.DataFrame, y: pd.Series):
        self.feature_columns = list(X.columns)
        self.model = self._build_model()
        self.model.fit(X, y)
        logger.info(f"Trained {self.model_type} on {len(X)} samples")

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        return self.model.predict(X)

    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        if hasattr(self.model, "predict_proba"):
            return self.model.predict_proba(X)
        raise AttributeError(f"{self.model_type} does not support predict_proba")

    def get_feature_importance(self) -> Dict[str, float]:
        if not hasattr(self.model, "feature_importances_"):
            if hasattr(self.model, "named_steps") and hasattr(self.model.named_steps.get("clf", None), "feature_importances_"):
                clf = self.model.named_steps["clf"]
                return dict(zip(self.feature_columns, clf.feature_importances_))
            return {}
        return dict(zip(self.feature_columns, self.model.feature_importances_))


class Evaluator:
    @staticmethod
    def evaluate_classification(y_true: pd.Series, y_pred: np.ndarray, y_proba: np.ndarray | None = None) -> Dict[str, Any]:
        metrics = {
            "accuracy": float(accuracy_score(y_true, y_pred)),
            "precision": float(precision_score(y_true, y_pred, zero_division=0)),
            "recall": float(recall_score(y_true, y_pred, zero_division=0)),
            "f1_score": float(f1_score(y_true, y_pred, zero_division=0)),
            "confusion_matrix": confusion_matrix(y_true, y_pred).tolist(),
        }
        if y_proba is not None and y_proba.shape[1] == 2:
            metrics["roc_auc"] = float(roc_auc_score(y_true, y_proba[:, 1]))
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
