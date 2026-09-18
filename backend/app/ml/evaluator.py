import logging
from typing import Dict, Any
import pandas as pd
import numpy as np
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score, confusion_matrix, mean_absolute_error, mean_squared_error, r2_score

logger = logging.getLogger(__name__)


class Evaluator:
    @staticmethod
    def evaluate_classification(y_true: pd.Series, y_pred: pd.Series, y_proba: pd.Series | None = None) -> Dict[str, Any]:
        metrics = {
            "accuracy": float(accuracy_score(y_true, y_pred)),
            "precision": float(precision_score(y_true, y_pred, zero_division=0)),
            "recall": float(recall_score(y_true, y_pred, zero_division=0)),
            "f1_score": float(f1_score(y_true, y_pred, zero_division=0)),
            "confusion_matrix": confusion_matrix(y_true, y_pred).tolist(),
        }
        if y_proba is not None:
            try:
                metrics["roc_auc"] = float(roc_auc_score(y_true, y_proba))
            except Exception as e:
                logger.warning(f"Could not compute ROC-AUC: {e}")
        return metrics

    @staticmethod
    def evaluate_regression(y_true: pd.Series, y_pred: pd.Series) -> Dict[str, Any]:
        mse = mean_squared_error(y_true, y_pred)
        return {
            "mae": float(mean_absolute_error(y_true, y_pred)),
            "rmse": float(np.sqrt(mse)),
            "r2": float(r2_score(y_true, y_pred)),
        }
