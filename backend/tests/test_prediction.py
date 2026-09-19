import pytest
import numpy as np
from datetime import date
from pathlib import Path



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
        term = await term_repo.create(SearchTermCreate(term="pred_term", category="test", active=True))
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


@pytest.mark.asyncio
async def test_classification_prediction_returns_direction(db_session):
    dates, closes = _build_training_rows(n=30)
    await _ingest_symbol(db_session, "CLSPRED", dates, closes)

    client = await _get_client(db_session)
    try:
        resp = await client.post("/api/features/generate", json={
            "symbol": "CLSPRED",
            "search_term_ids": [1],
            "start_date": date(2024, 1, 1).isoformat(),
            "end_date": date(2024, 1, 15).isoformat(),
        })
        assert resp.status_code == 200

        resp = await client.post("/api/models/train", json={
            "symbol": "CLSPRED",
            "start_date": "2024-01-01",
            "end_date": "2024-01-15",
            "task": "classification",
            "model_name": "logistic_regression",
        })
        assert resp.status_code == 200
        model_run_id = resp.json()["model_run_id"]

        prediction_date = date(2024, 1, 10)
        resp = await client.post("/api/models/predict", json={
            "model_run_id": model_run_id,
            "symbol": "CLSPRED",
            "prediction_date": prediction_date.isoformat(),
        })
        assert resp.status_code == 200
        body = resp.json()
        assert body["task_type"] == "classification"
        assert body["predicted_class"] in {0, 1}
        assert body["predicted_direction"] in {"Up", "Down"}
    finally:
        await _close_client(client)


@pytest.mark.asyncio
async def test_regression_prediction_returns_numeric_return(db_session):
    dates, closes = _build_training_rows(n=30)
    await _ingest_symbol(db_session, "REGPREP", dates, closes)

    client = await _get_client(db_session)
    try:
        resp = await client.post("/api/features/generate", json={
            "symbol": "REGPREP",
            "search_term_ids": [1],
            "start_date": date(2024, 1, 1).isoformat(),
            "end_date": date(2024, 1, 15).isoformat(),
        })
        assert resp.status_code == 200

        resp = await client.post("/api/models/train", json={
            "symbol": "REGPREP",
            "start_date": "2024-01-01",
            "end_date": "2024-01-15",
            "task": "regression",
            "model_name": "linear_regression",
        })
        assert resp.status_code == 200
        model_run_id = resp.json()["model_run_id"]

        prediction_date = date(2024, 1, 10)
        resp = await client.post("/api/models/predict", json={
            "model_run_id": model_run_id,
            "symbol": "REGPREP",
            "prediction_date": prediction_date.isoformat(),
        })
        assert resp.status_code == 200
        body = resp.json()
        assert body["task_type"] == "regression"
        assert isinstance(body["predicted_return"], float)
    finally:
        await _close_client(client)


@pytest.mark.asyncio
async def test_unknown_model_run_returns_error(db_session):
    client = await _get_client(db_session)
    try:
        resp = await client.post("/api/models/predict", json={
            "model_run_id": 99999,
            "symbol": "NONEXISTENT",
            "prediction_date": "2024-01-10",
        })
        assert resp.status_code == 400
    finally:
        await _close_client(client)


@pytest.mark.asyncio
async def test_missing_feature_row_returns_error(db_session):
    dates, closes = _build_training_rows(n=30)
    await _ingest_symbol(db_session, "MISSFEAT", dates, closes)

    client = await _get_client(db_session)
    try:
        resp = await client.post("/api/features/generate", json={
            "symbol": "MISSFEAT",
            "search_term_ids": [1],
            "start_date": date(2024, 1, 1).isoformat(),
            "end_date": date(2024, 1, 15).isoformat(),
        })
        assert resp.status_code == 200

        resp = await client.post("/api/models/train", json={
            "symbol": "MISSFEAT",
            "start_date": "2024-01-01",
            "end_date": "2024-01-15",
            "task": "classification",
            "model_name": "logistic_regression",
        })
        assert resp.status_code == 200
        model_run_id = resp.json()["model_run_id"]

        resp = await client.post("/api/models/predict", json={
            "model_run_id": model_run_id,
            "symbol": "MISSFEAT",
            "prediction_date": "1900-01-01",
        })
        assert resp.status_code == 400
    finally:
        await _close_client(client)


@pytest.mark.asyncio
async def test_symbol_mismatch_returns_error(db_session):
    dates, closes = _build_training_rows(n=30)
    await _ingest_symbol(db_session, "SYMMATCH", dates, closes)

    client = await _get_client(db_session)
    try:
        resp = await client.post("/api/features/generate", json={
            "symbol": "SYMMATCH",
            "search_term_ids": [1],
            "start_date": date(2024, 1, 1).isoformat(),
            "end_date": date(2024, 1, 15).isoformat(),
        })
        assert resp.status_code == 200

        resp = await client.post("/api/models/train", json={
            "symbol": "SYMMATCH",
            "start_date": "2024-01-01",
            "end_date": "2024-01-15",
            "task": "classification",
            "model_name": "logistic_regression",
        })
        assert resp.status_code == 200
        model_run_id = resp.json()["model_run_id"]

        resp = await client.post("/api/models/predict", json={
            "model_run_id": model_run_id,
            "symbol": "WRONGSYMBOL",
            "prediction_date": "2024-01-10",
        })
        assert resp.status_code == 400
    finally:
        await _close_client(client)


@pytest.mark.asyncio
async def test_artifact_persisted_after_training(db_session):
    dates, closes = _build_training_rows(n=30)
    await _ingest_symbol(db_session, "ARTPERSIST", dates, closes)

    client = await _get_client(db_session)
    try:
        resp = await client.post("/api/features/generate", json={
            "symbol": "ARTPERSIST",
            "search_term_ids": [1],
            "start_date": date(2024, 1, 1).isoformat(),
            "end_date": date(2024, 1, 15).isoformat(),
        })
        assert resp.status_code == 200

        resp = await client.post("/api/models/train", json={
            "symbol": "ARTPERSIST",
            "start_date": "2024-01-01",
            "end_date": "2024-01-15",
            "task": "classification",
            "model_name": "random_forest_classifier",
        })
        assert resp.status_code == 200
        body = resp.json()
        assert body["artifact_path"] is not None
        assert Path(body["artifact_path"]).exists()
    finally:
        await _close_client(client)


@pytest.mark.asyncio
async def test_repeated_predictions_are_reproducible(db_session):
    dates, closes = _build_training_rows(n=30)
    await _ingest_symbol(db_session, "REPRO", dates, closes)

    client = await _get_client(db_session)
    try:
        resp = await client.post("/api/features/generate", json={
            "symbol": "REPRO",
            "search_term_ids": [1],
            "start_date": date(2024, 1, 1).isoformat(),
            "end_date": date(2024, 1, 15).isoformat(),
        })
        assert resp.status_code == 200

        resp = await client.post("/api/models/train", json={
            "symbol": "REPRO",
            "start_date": "2024-01-01",
            "end_date": "2024-01-15",
            "task": "classification",
            "model_name": "random_forest_classifier",
        })
        assert resp.status_code == 200
        model_run_id = resp.json()["model_run_id"]

        prediction_date = date(2024, 1, 10)
        resp1 = await client.post("/api/models/predict", json={
            "model_run_id": model_run_id,
            "symbol": "REPRO",
            "prediction_date": prediction_date.isoformat(),
        })
        assert resp1.status_code == 200

        resp2 = await client.post("/api/models/predict", json={
            "model_run_id": model_run_id,
            "symbol": "REPRO",
            "prediction_date": prediction_date.isoformat(),
        })
        assert resp2.status_code == 200

        assert resp1.json()["predicted_class"] == resp2.json()["predicted_class"]
    finally:
        await _close_client(client)
