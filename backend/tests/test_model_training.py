from datetime import date

import numpy as np
import pandas as pd
import pytest
from httpx import ASGITransport, AsyncClient

from app.core.database import get_db
from app.main import app
from app.ml.model_trainer import (
    ModelTrainer,
)
from app.services.training_service import TrainingError, TrainingService


def _build_training_rows(n=30, seed=42):
    np.random.seed(seed)
    dates = [date(2024, 1, 1) + __import__("datetime").timedelta(days=i) for i in range(n)]
    base = 100.0
    closes = []
    for _ in range(n):
        change = np.random.randn() * 3
        base = base + change
        closes.append(base)
    return dates, closes


async def _ingest_symbol(db_session, symbol, dates, closes, search_term_ids=None):
    from app.repositories.market_data_repo import MarketDataRepository
    from app.repositories.search_term_repo import SearchTermRepository
    from app.repositories.trends_repo import TrendsRepository
    from app.schemas.search_terms import SearchTermCreate

    if search_term_ids is None:
        term_repo = SearchTermRepository(db_session)
        term = await term_repo.create(SearchTermCreate(term="train_term", category="test", active=True))
        search_term_ids = [term.id]

    market_repo = MarketDataRepository(db_session)
    await market_repo.bulk_insert([
        {"symbol": symbol, "date": d, "close": c, "volume": 1000, "open": c, "high": c, "low": c, "adj_close": c}
        for d, c in zip(dates, closes, strict=True)
    ])

    trends_repo = TrendsRepository(db_session)
    await trends_repo.bulk_insert([
        {"search_term_id": tid, "date": d, "interest_score": 10 + i * 5}
        for i, d in enumerate(dates)
        for tid in search_term_ids
    ])


async def _get_client(db_session):
    async def override_get_db():
        try:
            yield db_session
            await db_session.commit()
        except Exception:
            await db_session.rollback()
            raise

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    client = AsyncClient(transport=transport, base_url="http://test", follow_redirects=True)
    return client


async def _close_client(client):
    await client.aclose()
    app.dependency_overrides.pop(get_db, None)


def test_logistic_regression_creation():
    trainer = ModelTrainer(model_name="logistic_regression", task_type="classification")
    assert trainer.model_name == "logistic_regression"
    assert trainer.task_type == "classification"


def test_random_forest_classifier_creation():
    trainer = ModelTrainer(model_name="random_forest_classifier", task_type="classification")
    assert trainer.model_name == "random_forest_classifier"
    assert trainer.task_type == "classification"


def test_linear_regression_creation():
    trainer = ModelTrainer(model_name="linear_regression", task_type="regression")
    assert trainer.model_name == "linear_regression"
    assert trainer.task_type == "regression"


def test_random_forest_regressor_creation():
    trainer = ModelTrainer(model_name="random_forest_regressor", task_type="regression")
    assert trainer.model_name == "random_forest_regressor"
    assert trainer.task_type == "regression"


@pytest.mark.asyncio
async def test_classification_training_completes(db_session):
    dates, closes = _build_training_rows(n=30)
    await _ingest_symbol(db_session, "CLSTRAIN", dates, closes)

    client = await _get_client(db_session)
    try:
        resp = await client.post("/api/features/generate", json={
            "symbol": "CLSTRAIN",
            "search_term_ids": [1],
            "start_date": date(2024, 1, 1).isoformat(),
            "end_date": date(2024, 1, 15).isoformat(),
        })
        assert resp.status_code == 200
    finally:
        await _close_client(client)

    service = TrainingService(db_session, "CLSTRAIN", date(2024, 1, 1), date(2024, 1, 15), "classification", "logistic_regression")
    result = await service.train()
    assert result["training_completed"] is True
    assert result["training_rows"] > 0
    assert result["feature_count"] > 0
    assert result["target_name"] == "next_day_direction"


@pytest.mark.asyncio
async def test_regression_training_completes(db_session):
    dates, closes = _build_training_rows(n=30)
    await _ingest_symbol(db_session, "REGTRAIN", dates, closes)

    client = await _get_client(db_session)
    try:
        resp = await client.post("/api/features/generate", json={
            "symbol": "REGTRAIN",
            "search_term_ids": [1],
            "start_date": date(2024, 1, 1).isoformat(),
            "end_date": date(2024, 1, 15).isoformat(),
        })
        assert resp.status_code == 200
    finally:
        await _close_client(client)

    service = TrainingService(db_session, "REGTRAIN", date(2024, 1, 1), date(2024, 1, 15), "regression", "linear_regression")
    result = await service.train()
    assert result["training_completed"] is True
    assert result["training_rows"] > 0
    assert result["target_name"] == "next_day_return"


@pytest.mark.asyncio
async def test_prediction_shape_matches_test_rows(db_session):
    dates, closes = _build_training_rows(n=30)
    await _ingest_symbol(db_session, "SHAPE", dates, closes)

    client = await _get_client(db_session)
    try:
        resp = await client.post("/api/features/generate", json={
            "symbol": "SHAPE",
            "search_term_ids": [1],
            "start_date": date(2024, 1, 1).isoformat(),
            "end_date": date(2024, 1, 15).isoformat(),
        })
        assert resp.status_code == 200
    finally:
        await _close_client(client)

    service = TrainingService(db_session, "SHAPE", date(2024, 1, 1), date(2024, 1, 15), "classification", "random_forest_classifier")
    result = await service.train()
    assert result["test_prediction_shape"][0] == result["test_rows"]
    assert result["validation_prediction_shape"][0] == result["validation_rows"]
    assert result["train_prediction_shape"][0] == result["training_rows"]


def test_invalid_classification_target_rejected():
    service = TrainingService(None, "X", date(2024, 1, 1), date(2024, 1, 10), "classification", "logistic_regression")
    with pytest.raises(TrainingError, match="invalid values"):
        service._validate_classification_target(pd.Series([0, 1, 2]), "training")


def test_nan_regression_target_rejected():
    service = TrainingService(None, "X", date(2024, 1, 1), date(2024, 1, 10), "regression", "linear_regression")
    with pytest.raises(TrainingError, match="NaN"):
        service._validate_regression_target(pd.Series([1.0, np.nan, 2.0]), "training")


def test_infinite_regression_target_rejected():
    service = TrainingService(None, "X", date(2024, 1, 1), date(2024, 1, 10), "regression", "linear_regression")
    with pytest.raises(TrainingError, match="infinite"):
        service._validate_regression_target(pd.Series([1.0, np.inf, 2.0]), "training")


@pytest.mark.asyncio
async def test_target_excluded_from_features(db_session):
    dates, closes = _build_training_rows(n=30)
    await _ingest_symbol(db_session, "SEP2", dates, closes)

    client = await _get_client(db_session)
    try:
        resp = await client.post("/api/features/generate", json={
            "symbol": "SEP2",
            "search_term_ids": [1],
            "start_date": date(2024, 1, 1).isoformat(),
            "end_date": date(2024, 1, 15).isoformat(),
        })
        assert resp.status_code == 200
    finally:
        await _close_client(client)

    from app.services.ml_dataset_service import MLDatasetService
    ml_service = MLDatasetService(db_session)
    splits = await ml_service.get_splits("SEP2", date(2024, 1, 1), date(2024, 1, 15))
    assert "next_day_return" not in splits["feature_names"]
    assert "next_day_direction" not in splits["feature_names"]


def test_scaler_fitted_only_on_train_data():
    np.random.seed(42)
    X_train = pd.DataFrame({"a": np.random.randn(20), "b": np.random.randn(20)})
    X_test = pd.DataFrame({"a": np.random.randn(5), "b": np.random.randn(5)})

    trainer = ModelTrainer(model_name="logistic_regression", task_type="classification")
    y = pd.Series(np.random.randint(0, 2, size=20))
    trainer.train(X_train, y)

    predictions = trainer.predict(X_test)
    assert len(predictions) == 5


def test_deterministic_random_forest():
    np.random.seed(42)
    X = pd.DataFrame({"a": np.random.randn(30), "b": np.random.randn(30)})
    y = pd.Series(np.random.randint(0, 2, size=30))

    trainer1 = ModelTrainer(model_name="random_forest_classifier", task_type="classification", random_state=42)
    trainer1.train(X, y)
    pred1 = trainer1.predict(X)

    trainer2 = ModelTrainer(model_name="random_forest_classifier", task_type="classification", random_state=42)
    trainer2.train(X, y)
    pred2 = trainer2.predict(X)

    assert np.array_equal(pred1, pred2)


def test_classification_rejects_regression_model():
    with pytest.raises(ValueError, match="Unsupported classification model"):
        ModelTrainer(model_name="linear_regression", task_type="classification")


def test_regression_rejects_classification_model():
    with pytest.raises(ValueError, match="Unsupported regression model"):
        ModelTrainer(model_name="logistic_regression", task_type="regression")


def test_unknown_task_rejected():
    with pytest.raises(ValueError, match="Unsupported task type"):
        ModelTrainer(model_name="logistic_regression", task_type="unknown")


@pytest.mark.asyncio
async def test_api_invalid_combination_rejected(db_session):
    client = await _get_client(db_session)
    try:
        resp = await client.post("/api/models/train", json={
            "symbol": "NONEXISTENT",
            "start_date": "2024-01-01",
            "end_date": "2024-06-30",
            "task": "classification",
            "model_name": "linear_regression",
        })
        assert resp.status_code == 400
    finally:
        await _close_client(client)


@pytest.mark.asyncio
async def test_insufficient_training_rows_rejected(db_session):
    from app.repositories.market_data_repo import MarketDataRepository
    from app.repositories.search_term_repo import SearchTermRepository
    from app.repositories.trends_repo import TrendsRepository
    from app.schemas.search_terms import SearchTermCreate

    term_repo = SearchTermRepository(db_session)
    term = await term_repo.create(SearchTermCreate(term="insuff_train", category="test", active=True))

    market_repo = MarketDataRepository(db_session)
    await market_repo.bulk_insert([
        {"symbol": "INSUFF", "date": date(2024, 1, 1), "close": 100.0, "volume": 1000, "open": 100.0, "high": 100.0, "low": 100.0, "adj_close": 100.0},
        {"symbol": "INSUFF", "date": date(2024, 1, 2), "close": 110.0, "volume": 1100, "open": 110.0, "high": 110.0, "low": 110.0, "adj_close": 110.0},
        {"symbol": "INSUFF", "date": date(2024, 1, 3), "close": 105.0, "volume": 1200, "open": 105.0, "high": 105.0, "low": 105.0, "adj_close": 105.0},
    ])

    trends_repo = TrendsRepository(db_session)
    await trends_repo.bulk_insert([
        {"search_term_id": term.id, "date": date(2024, 1, 1), "interest_score": 10},
        {"search_term_id": term.id, "date": date(2024, 1, 2), "interest_score": 20},
        {"search_term_id": term.id, "date": date(2024, 1, 3), "interest_score": 30},
    ])

    client = await _get_client(db_session)
    try:
        resp = await client.post("/api/features/generate", json={
            "symbol": "INSUFF",
            "search_term_ids": [term.id],
            "start_date": "2024-01-01",
            "end_date": "2024-01-03",
        })
        assert resp.status_code == 400
    finally:
        await _close_client(client)


@pytest.mark.asyncio
async def test_api_success(db_session):
    dates, closes = _build_training_rows(n=30)
    await _ingest_symbol(db_session, "APITRAIN", dates, closes)

    client = await _get_client(db_session)
    try:
        resp = await client.post("/api/features/generate", json={
            "symbol": "APITRAIN",
            "search_term_ids": [1],
            "start_date": date(2024, 1, 1).isoformat(),
            "end_date": date(2024, 1, 15).isoformat(),
        })
        assert resp.status_code == 200

        resp = await client.post("/api/models/train", json={
            "symbol": "APITRAIN",
            "start_date": "2024-01-01",
            "end_date": "2024-01-15",
            "task": "classification",
            "model_name": "logistic_regression",
        })
        assert resp.status_code == 200
        body = resp.json()
        assert body["model_name"] == "logistic_regression"
        assert body["task_type"] == "classification"
        assert body["training_completed"] is True
        assert body["feature_count"] > 0
    finally:
        await _close_client(client)


@pytest.mark.asyncio
async def test_api_validation_error(db_session):
    dates, closes = _build_training_rows(n=30)
    await _ingest_symbol(db_session, "APITRAIN2", dates, closes)

    client = await _get_client(db_session)
    try:
        resp = await client.post("/api/features/generate", json={
            "symbol": "APITRAIN2",
            "search_term_ids": [1],
            "start_date": date(2024, 1, 1).isoformat(),
            "end_date": date(2024, 1, 15).isoformat(),
        })
        assert resp.status_code == 200

        resp = await client.post("/api/models/train", json={
            "symbol": "APITRAIN2",
            "start_date": "2024-01-01",
            "end_date": "2024-01-15",
            "task": "classification",
            "model_name": "linear_regression",
        })
        assert resp.status_code == 400
    finally:
        await _close_client(client)
