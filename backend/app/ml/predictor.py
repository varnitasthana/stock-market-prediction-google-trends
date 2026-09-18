import logging
from typing import Dict, Any, Optional
import pandas as pd
import numpy as np
from app.ml.model_trainer import ModelTrainer, Evaluator

logger = logging.getLogger(__name__)


class Predictor:
    def __init__(self):
        self.trainer: Optional[ModelTrainer] = None
        self.feature_columns: list[str] = []

    def load_model(self, trainer: ModelTrainer):
        self.trainer = trainer
        self.feature_columns = trainer.feature_columns

    def predict(self, features: pd.DataFrame) -> Dict[str, Any]:
        if self.trainer is None:
            raise RuntimeError("Model not loaded")
        X = features[self.feature_columns].fillna(0)
        direction = int(self.trainer.predict(X)[0])
        proba = self.trainer.predict_proba(X)[0]
        return {
            "predicted_direction": direction,
            "probability": float(proba[1]),
            "confidence": float(max(proba)),
        }
