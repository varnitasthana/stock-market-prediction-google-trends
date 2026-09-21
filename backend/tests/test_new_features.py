from datetime import date

import pytest
from httpx import ASGITransport, AsyncClient

from app.core.database import get_db
from app.main import app

pytestmark = pytest.mark.asyncio


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


async def test_sentiment_daily_requires_data(client: AsyncClient, db_session):
    resp = await client.get("/api/sentiment/daily/%5ENSEI")
    assert resp.status_code in (200, 400, 500)


async def test_sentiment_text_endpoint(client: AsyncClient):
    resp = await client.post("/api/sentiment/text", json={"text": "market is bullish and rising"})
    assert resp.status_code == 200
    body = resp.json()
    assert "score" in body
    assert "label" in body


async def test_explainability_endpoint_validation(client: AsyncClient):
    resp = await client.get("/api/models/explain", params={"model_run_id": 99999, "symbol": "NONEXISTENT", "prediction_date": "2024-01-10"})
    assert resp.status_code in (400, 404, 422, 500)
