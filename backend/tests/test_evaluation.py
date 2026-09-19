import pytest
import pandas as pd
import numpy as np
from datetime import date

from app.ml.model_trainer import Evaluator
from app.services.evaluation_service import EvaluationService, EvaluationError



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
    from app.repositories.search_term_repo import SearchTermRepository
    from app.repositories.market_data_repo import MarketDataRepository
    from app.repositories.trends_repo import TrendsRepository
    from app.schemas.search_terms import SearchTermCreate

    if search_term_ids is None:
        term_repo = SearchTermRepository(db_session)
        term = await term_repo.create(SearchTermCreate(term="eval_term", category="test", active=True))
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

    from app.core.database import get_db
    from httpx import AsyncClient, ASGITransport
    from app.main import app

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    client = AsyncClient(transport=transport, base_url="http://test", follow_redirects=True)
    return client


async def _close_client(client):
    await client.aclose()
    from app.main import app
    from app.core.database import get_db
    app.dependency_overrides.pop(get_db, None)


def test_classification_metrics_deterministic():
    y_true = pd.Series([0, 1, 0, 1, 0, 1, 0, 1])
    y_pred = np.array([0, 1, 0, 1, 0, 1, 0, 1])
    y_proba = np.array([[0.8, 0.2], [0.3, 0.7], [0.9, 0.1], [0.2, 0.8], [0.7, 0.3], [0.4, 0.6], [0.6, 0.4], [0.1, 0.9]])

    metrics = Evaluator.evaluate_classification(y_true, y_pred, y_proba)
    assert metrics["accuracy"] == 1.0
    assert metrics["precision"] == 1.0
    assert metrics["recall"] == 1.0
    assert metrics["f1_score"] == 1.0


def test_regression_metrics_deterministic():
    y_true = pd.Series([1.0, 2.0, 3.0, 4.0])
    y_pred = np.array([1.1, 2.0, 2.9, 4.2])

    metrics = Evaluator.evaluate_regression(y_true, y_pred)
    assert abs(metrics["mae"] - 0.1) < 1e-6
    assert abs(metrics["rmse"] - np.sqrt(0.015)) < 1e-6
    assert abs(metrics["r2"] - 0.988) < 0.01


def test_confusion_matrix_structure():
    y_true = pd.Series([0, 0, 1, 1])
    y_pred = np.array([0, 1, 0, 1])
    metrics = Evaluator.evaluate_classification(y_true, y_pred)
    cm = metrics["confusion_matrix"]
    assert len(cm) == 2
    assert len(cm[0]) == 2
    assert cm[0][0] == 1
    assert cm[0][1] == 1
    assert cm[1][0] == 1
    assert cm[1][1] == 1


@pytest.mark.asyncio
async def test_validation_evaluation(db_session):
    dates, closes = _build_training_rows(n=30)
    await _ingest_symbol(db_session, "VALEVAL", dates, closes)

    client = await _get_client(db_session)
    try:
        resp = await client.post("/api/features/generate", json={
            "symbol": "VALEVAL",
            "search_term_ids": [1],
            "start_date": date(2024, 1, 1).isoformat(),
            "end_date": date(2024, 1, 15).isoformat(),
        })
        assert resp.status_code == 200

        resp = await client.post("/api/models/train", json={
            "symbol": "VALEVAL",
            "start_date": "2024-01-01",
            "end_date": "2024-01-15",
            "task": "classification",
            "model_name": "logistic_regression",
        })
        assert resp.status_code == 200
        model_run_id = resp.json()["model_run_id"]

        resp = await client.post("/api/models/evaluate", json={
            "model_run_id": model_run_id,
            "evaluation_split": "validation",
        })
        print(f"EVAL RESP: {resp.status_code} {resp.text}")
        assert resp.status_code == 200
        body = resp.json()
        assert body["split"] == "validation"
        assert body["sample_count"] > 0
    finally:
        await _close_client(client)


@pytest.mark.asyncio
async def test_test_evaluation(db_session):
    dates, closes = _build_training_rows(n=30)
    await _ingest_symbol(db_session, "TESTEVAL", dates, closes)

    client = await _get_client(db_session)
    try:
        resp = await client.post("/api/features/generate", json={
            "symbol": "TESTEVAL",
            "search_term_ids": [1],
            "start_date": date(2024, 1, 1).isoformat(),
            "end_date": date(2024, 1, 15).isoformat(),
        })
        assert resp.status_code == 200

        resp = await client.post("/api/models/train", json={
            "symbol": "TESTEVAL",
            "start_date": "2024-01-01",
            "end_date": "2024-01-15",
            "task": "regression",
            "model_name": "linear_regression",
        })
        assert resp.status_code == 200
        model_run_id = resp.json()["model_run_id"]

        resp = await client.post("/api/models/evaluate", json={
            "model_run_id": model_run_id,
            "evaluation_split": "test",
        })
        assert resp.status_code == 200
        body = resp.json()
        assert body["split"] == "test"
        assert body["sample_count"] > 0
        assert body["mae"] is not None
        assert body["rmse"] is not None
        assert body["r2"] is not None
    finally:
        await _close_client(client)


def test_class_distribution():
    y = pd.Series([0, 0, 0, 1, 1])
    result = EvaluationService._class_distribution(y)
    assert result["class_0_count"] == 3
    assert result["class_1_count"] == 2
    assert abs(result["class_0_percentage"] - 0.6) < 1e-6
    assert abs(result["class_1_percentage"] - 0.4) < 1e-6


def test_majority_baseline():
    y = pd.Series([0, 0, 0, 1, 1])
    result = EvaluationService._majority_class_baseline(y)
    assert result["predicted_class"] == 0
    assert abs(result["accuracy"] - 0.6) < 1e-6


def test_mean_baseline():
    y = pd.Series([1.0, 2.0, 3.0, 4.0])
    result = EvaluationService._mean_baseline(y)
    assert abs(result["predicted_value"] - 2.5) < 1e-6
    assert abs(result["mae"] - 1.0) < 1e-6


def test_invalid_split_rejected():
    service = EvaluationService(None, model_run_id=1, split="invalid")
    with pytest.raises(EvaluationError, match="Unsupported split"):
        import asyncio
        asyncio.run(service.evaluate())


def test_invalid_model_run_rejected():
    service = EvaluationService(None, model_run_id=99999, split="test")
    with pytest.raises((EvaluationError, Exception)):
        import asyncio
        asyncio.run(service.evaluate())


@pytest.mark.asyncio
async def test_api_success(db_session):
    dates, closes = _build_training_rows(n=30)
    await _ingest_symbol(db_session, "EVALAPI", dates, closes)

    client = await _get_client(db_session)
    try:
        resp = await client.post("/api/features/generate", json={
            "symbol": "EVALAPI",
            "search_term_ids": [1],
            "start_date": date(2024, 1, 1).isoformat(),
            "end_date": date(2024, 1, 15).isoformat(),
        })
        assert resp.status_code == 200

        resp = await client.post("/api/models/train", json={
            "symbol": "EVALAPI",
            "start_date": "2024-01-01",
            "end_date": "2024-01-15",
            "task": "classification",
            "model_name": "logistic_regression",
        })
        assert resp.status_code == 200
        model_run_id = resp.json()["model_run_id"]

        resp = await client.post("/api/models/evaluate", json={
            "model_run_id": model_run_id,
            "evaluation_split": "test",
        })
        assert resp.status_code == 200
        body = resp.json()
        assert body["model_run_id"] == model_run_id
        assert body["task_type"] == "classification"
        assert body["split"] == "test"
    finally:
        await _close_client(client)


@pytest.mark.asyncio
async def test_api_error_invalid_split(db_session):
    dates, closes = _build_training_rows(n=30)
    await _ingest_symbol(db_session, "EVALERR", dates, closes)

    client = await _get_client(db_session)
    try:
        resp = await client.post("/api/features/generate", json={
            "symbol": "EVALERR",
            "search_term_ids": [1],
            "start_date": date(2024, 1, 1).isoformat(),
            "end_date": date(2024, 1, 15).isoformat(),
        })
        assert resp.status_code == 200

        resp = await client.post("/api/models/train", json={
            "symbol": "EVALERR",
            "start_date": "2024-01-01",
            "end_date": "2024-01-15",
            "task": "classification",
            "model_name": "logistic_regression",
        })
        assert resp.status_code == 200
        model_run_id = resp.json()["model_run_id"]

        resp = await client.post("/api/models/evaluate", json={
            "model_run_id": model_run_id,
            "evaluation_split": "invalid",
        })
        assert resp.status_code == 400
    finally:
        await _close_client(client)


@pytest.mark.asyncio
async def test_regression_evaluation_metrics(db_session):
    dates, closes = _build_training_rows(n=30)
    await _ingest_symbol(db_session, "REGEVAL", dates, closes)

    client = await _get_client(db_session)
    try:
        resp = await client.post("/api/features/generate", json={
            "symbol": "REGEVAL",
            "search_term_ids": [1],
            "start_date": date(2024, 1, 1).isoformat(),
            "end_date": date(2024, 1, 15).isoformat(),
        })
        assert resp.status_code == 200

        resp = await client.post("/api/models/train", json={
            "symbol": "REGEVAL",
            "start_date": "2024-01-01",
            "end_date": "2024-01-15",
            "task": "regression",
            "model_name": "random_forest_regressor",
        })
        assert resp.status_code == 200
        model_run_id = resp.json()["model_run_id"]

        resp = await client.post("/api/models/evaluate", json={
            "model_run_id": model_run_id,
            "evaluation_split": "validation",
        })
        assert resp.status_code == 200
        body = resp.json()
        assert body["task_type"] == "regression"
        assert body["mae"] is not None
        assert body["rmse"] is not None
        assert body["r2"] is not None or body["sample_count"] < 5
        assert body["baseline"] is not None
        assert body["baseline"]["strategy"] == "training_mean"
    finally:
        await _close_client(client)
