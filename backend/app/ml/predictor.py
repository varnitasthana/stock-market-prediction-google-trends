import logging
from typing import Any

import pandas as pd

from app.ml.model_trainer import ModelTrainer

logger = logging.getLogger(__name__)


class Predictor:
    def __init__(self):
        self.trainer: ModelTrainer | None = None
        self.feature_columns: list[str] = []

    def load_model(self, trainer: ModelTrainer):
        self.trainer = trainer
        self.feature_columns = trainer.feature_columns

    def predict(self, features: pd.DataFrame) -> dict[str, Any]:
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
