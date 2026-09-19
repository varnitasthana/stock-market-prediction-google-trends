import logging
from datetime import date
from typing import List, Dict, Any, Optional, Tuple
import pandas as pd
import numpy as np

from app.repositories.features_repo import FeaturesRepository
from app.services.statistical_analysis_service import StatisticalAnalysisService

logger = logging.getLogger(__name__)


class MLDatasetError(Exception):
    pass


class MLDatasetService:
    def __init__(self, db):
        self.features_repo = FeaturesRepository(db)

    async def prepare_dataset(
        self,
        symbol: str,
        start_date: date,
        end_date: date,
        train_ratio: float = 0.70,
        validation_ratio: float = 0.15,
        test_ratio: float = 0.15,
    ) -> Dict[str, Any]:
        rows = await self.features_repo.get_by_symbol_and_date_range(symbol, start_date, end_date)
        if not rows:
            raise MLDatasetError(f"No engineered features found for {symbol} in range {start_date} to {end_date}")

        wide_df = self._pivot_to_wide(rows)
        if wide_df.empty:
            raise MLDatasetError("Engineered features are empty after pivoting")

        original_rows = len(wide_df)

        quality = self._validate_and_clean(wide_df)
        wide_df = quality["df"]
        rows_removed = quality["rows_removed"]

        feature_columns = self._identify_feature_columns(wide_df.columns.tolist())
        target_columns = self._identify_target_columns(wide_df.columns.tolist())

        missing_features = set(feature_columns) - set(wide_df.columns)
        missing_targets = set(target_columns) - set(wide_df.columns)
        if missing_features:
            raise MLDatasetError(f"Missing feature columns: {missing_features}")
        if missing_targets:
            raise MLDatasetError(f"Missing target columns: {missing_targets}")

        leakage_check = self._check_leakage(wide_df.columns.tolist(), feature_columns, target_columns)
        if not leakage_check["safe"]:
            raise MLDatasetError(f"Leakage detected: {leakage_check['issues']}")

        splits = self._chronological_split(wide_df, train_ratio, validation_ratio, test_ratio)

        X_train = wide_df.loc[splits["train_indices"], feature_columns].reset_index(drop=True)
        y_train_classification = wide_df.loc[splits["train_indices"], "next_day_direction"].reset_index(drop=True)
        y_train_regression = wide_df.loc[splits["train_indices"], "next_day_return"].reset_index(drop=True)

        X_validation = wide_df.loc[splits["validation_indices"], feature_columns].reset_index(drop=True)
        y_validation_classification = wide_df.loc[splits["validation_indices"], "next_day_direction"].reset_index(drop=True)
        y_validation_regression = wide_df.loc[splits["validation_indices"], "next_day_return"].reset_index(drop=True)

        X_test = wide_df.loc[splits["test_indices"], feature_columns].reset_index(drop=True)
        y_test_classification = wide_df.loc[splits["test_indices"], "next_day_direction"].reset_index(drop=True)
        y_test_regression = wide_df.loc[splits["test_indices"], "next_day_return"].reset_index(drop=True)

        train_dates = wide_df.loc[splits["train_indices"], "date"]
        validation_dates = wide_df.loc[splits["validation_indices"], "date"]
        test_dates = wide_df.loc[splits["test_indices"], "date"]

        train_quality = self._validate_targets(y_train_classification, y_train_regression)
        validation_quality = self._validate_targets(y_validation_classification, y_validation_regression)
        test_quality = self._validate_targets(y_test_classification, y_test_regression)

        all_quality_issues = train_quality["issues"] + validation_quality["issues"] + test_quality["issues"]
        if all_quality_issues:
            raise MLDatasetError(f"Target validation issues: {all_quality_issues}")

        return {
            "symbol": symbol,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "original_rows": int(original_rows),
            "rows_after_cleaning": int(len(wide_df)),
            "rows_removed": int(rows_removed),
            "feature_count": len(feature_columns),
            "feature_names": feature_columns,
            "target_names": ["next_day_return", "next_day_direction"],
            "train_rows": int(len(X_train)),
            "validation_rows": int(len(X_validation)),
            "test_rows": int(len(X_test)),
            "train_start_date": train_dates.iloc[0].isoformat() if len(train_dates) > 0 else None,
            "train_end_date": train_dates.iloc[-1].isoformat() if len(train_dates) > 0 else None,
            "validation_start_date": validation_dates.iloc[0].isoformat() if len(validation_dates) > 0 else None,
            "validation_end_date": validation_dates.iloc[-1].isoformat() if len(validation_dates) > 0 else None,
            "test_start_date": test_dates.iloc[0].isoformat() if len(test_dates) > 0 else None,
            "test_end_date": test_dates.iloc[-1].isoformat() if len(test_dates) > 0 else None,
            "train_ratio": train_ratio,
            "validation_ratio": validation_ratio,
            "test_ratio": test_ratio,
            "leakage_safe": True,
            "quality_issues": all_quality_issues,
            "X_train_shape": list(X_train.shape),
            "X_validation_shape": list(X_validation.shape),
            "X_test_shape": list(X_test.shape),
        }

    @staticmethod
    def _pivot_to_wide(rows) -> pd.DataFrame:
        records = []
        for r in rows:
            records.append({
                "date": r.date,
                "feature_name": r.feature_name,
                "feature_value": float(r.feature_value) if r.feature_value is not None else np.nan,
            })
        if not records:
            return pd.DataFrame()
        df = pd.DataFrame(records)
        wide = df.pivot_table(index="date", columns="feature_name", values="feature_value", aggfunc="first")
        wide = wide.reset_index()
        wide["date"] = pd.to_datetime(wide["date"])
        wide = wide.dropna(subset=["date"])
        wide = wide.sort_values("date").reset_index(drop=True)
        return wide

    @staticmethod
    def _validate_and_clean(df: pd.DataFrame) -> Dict[str, Any]:
        df = df.copy()
        original_rows = len(df)

        duplicate_dates = df.duplicated(subset=["date"], keep=False)
        duplicate_count = int(duplicate_dates.sum())
        if duplicate_count > 0:
            logger.warning("Found %d duplicate date rows, keeping first occurrence", duplicate_count)
            df = df.drop_duplicates(subset=["date"], keep="first").reset_index(drop=True)

        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        for col in numeric_cols:
            if col in {"next_day_direction"}:
                continue
            inf_mask = np.isinf(df[col])
            if inf_mask.any():
                logger.warning("Column %s contains %d infinite values, replacing with NaN", col, int(inf_mask.sum()))
                df.loc[inf_mask, col] = np.nan

        required_cols = {"next_day_return", "next_day_direction"}
        missing_required = required_cols - set(df.columns)
        if missing_required:
            raise MLDatasetError(f"Missing required columns: {missing_required}")

        before_drop = len(df)
        df = df.dropna(subset=["next_day_return", "next_day_direction"]).reset_index(drop=True)
        rows_removed = original_rows - len(df) + (original_rows - before_drop)

        return {"df": df, "rows_removed": rows_removed, "duplicate_count": duplicate_count}

    @staticmethod
    def _identify_feature_columns(columns: List[str]) -> List[str]:
        exclude = {"date", "symbol", "next_day_return", "next_day_direction"}
        feature_cols = [c for c in columns if c not in exclude]
        return sorted(feature_cols)

    @staticmethod
    def _identify_target_columns(columns: List[str]) -> List[str]:
        required = {"next_day_return", "next_day_direction"}
        return [c for c in columns if c in required]

    @staticmethod
    def _check_leakage(columns: List[str], feature_columns: List[str], target_columns: List[str]) -> Dict[str, Any]:
        issues = []
        for col in feature_columns:
            if col in target_columns:
                issues.append(f"Feature column '{col}' is also a target column")
        for col in target_columns:
            if col not in columns:
                issues.append(f"Target column '{col}' missing from dataset")
        future_indicators = ["future", "forward", "target", "label"]
        for col in feature_columns:
            for indicator in future_indicators:
                if indicator in col.lower() and col not in {"next_day_return", "next_day_direction"}:
                    issues.append(f"Feature column '{col}' may be future-looking")
        return {"safe": len(issues) == 0, "issues": issues}

    @staticmethod
    def _chronological_split(df: pd.DataFrame, train_ratio: float, validation_ratio: float, test_ratio: float) -> Dict[str, Any]:
        total = len(df)
        if total < 3:
            raise MLDatasetError(f"Insufficient observations ({total}) for train/validation/test split")

        if total == 3:
            train_size, validation_size, test_size = 1, 1, 1
        elif total == 4:
            train_size, validation_size, test_size = 2, 1, 1
        else:
            train_size = max(1, int(np.floor(total * train_ratio)))
            remaining = total - train_size
            val_fraction = validation_ratio / (validation_ratio + test_ratio) if (validation_ratio + test_ratio) > 0 else 0.5
            validation_size = max(1, int(np.floor(remaining * val_fraction)))
            test_size = total - train_size - validation_size
            if test_size < 1:
                test_size = 1
                validation_size = max(1, total - train_size - test_size)
                if validation_size < 1:
                    validation_size = 1
                    train_size = max(1, total - validation_size - test_size)

        train_indices = list(range(0, train_size))
        validation_indices = list(range(train_size, train_size + validation_size))
        test_indices = list(range(train_size + validation_size, total))

        train_dates = df.loc[train_indices, "date"]
        validation_dates = df.loc[validation_indices, "date"]
        test_dates = df.loc[test_indices, "date"]

        if len(train_dates) > 0 and len(validation_dates) > 0:
            if train_dates.iloc[-1] >= validation_dates.iloc[0]:
                raise MLDatasetError("Train and validation sets overlap chronologically")
        if len(validation_dates) > 0 and len(test_dates) > 0:
            if validation_dates.iloc[-1] >= test_dates.iloc[0]:
                raise MLDatasetError("Validation and test sets overlap chronologically")

        return {
            "train_indices": train_indices,
            "validation_indices": validation_indices,
            "test_indices": test_indices,
        }

    @staticmethod
    def _validate_targets(y_classification: pd.Series, y_regression: pd.Series) -> Dict[str, Any]:
        issues = []
        unique_classes = set(y_classification.dropna().unique())
        if not unique_classes.issubset({0, 1}):
            issues.append(f"Classification target contains invalid values: {unique_classes - {0, 1}}")
        if y_regression.isna().any():
            issues.append("Regression target contains NaN values")
        if np.isinf(y_regression).any():
            issues.append("Regression target contains infinite values")
        return {"valid": len(issues) == 0, "issues": issues}
