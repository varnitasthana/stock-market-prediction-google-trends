import pytest
import pytest_asyncio
from httpx import AsyncClient
import pandas as pd
from datetime import date
from sqlalchemy.ext.asyncio import AsyncSession

from app.main import app
from app.pipeline.trends_provider import TrendsDataProvider, PytrendsProvider
from app.pipeline.trends_pipeline import TrendsIngestionService, TrendsError
from app.schemas.trends import TrendsIngestRequest
from app.core.database import get_db

from tests.conftest import client, db_session


class FakeProvider(TrendsDataProvider):
    def __init__(self, data: pd.DataFrame | None = None, fail: bool = False):
        self.data = data
        self.fail = fail
        self.calls = []

    async def fetch_term(self, term: str, start_date: str, end_date: str) -> pd.DataFrame:
        self.calls.append((term, start_date, end_date))
        if self.fail:
            raise RuntimeError("provider unavailable")
        if self.data is None:
            return pd.DataFrame({"date": [], "interest_score": []})
        return self.data.copy()


@pytest.mark.asyncio
async def test_fake_provider_returns_records():
    df = pd.DataFrame({
        "date": [pd.Timestamp("2024-01-01").date(), pd.Timestamp("2024-01-02").date()],
        "interest_score": [10, 20],
    })
    provider = FakeProvider(data=df)
    result = await provider.fetch_term("test", "2024-01-01", "2024-01-02")
    assert len(result) == 2
    assert list(result["interest_score"]) == [10, 20]


@pytest.mark.asyncio
async def test_fake_provider_returns_empty():
    provider = FakeProvider()
    result = await provider.fetch_term("test", "2024-01-01", "2024-01-02")
    assert result.empty


@pytest.mark.asyncio
async def test_fake_provider_failure():
    provider = FakeProvider(fail=True)
    with pytest.raises(RuntimeError, match="provider unavailable"):
        await provider.fetch_term("test", "2024-01-01", "2024-01-02")


@pytest.mark.asyncio
async def test_ingest_term_inserts_records(client: AsyncClient, db_session: AsyncSession):
    df = pd.DataFrame({
        "date": [pd.Timestamp("2024-01-01").date(), pd.Timestamp("2024-01-02").date()],
        "interest_score": [10, 20],
    })
    provider = FakeProvider(data=df)

    create_resp = await client.post("/api/search-terms/", json={"term": "trends_test", "category": "test"})
    assert create_resp.status_code == 201

    service = TrendsIngestionService(db_session, provider)
    result = await service.ingest_term("trends_test", "2024-01-01", "2024-01-02")
    assert result["inserted"] == 2
    assert result["total_records"] == 2


@pytest.mark.asyncio
async def test_ingest_term_skips_duplicates(client: AsyncClient, db_session: AsyncSession):
    df = pd.DataFrame({
        "date": [pd.Timestamp("2024-01-01").date(), pd.Timestamp("2024-01-02").date()],
        "interest_score": [10, 20],
    })
    provider = FakeProvider(data=df)

    service = TrendsIngestionService(db_session, provider)
    result1 = await service.ingest_term("trends_dup", "2024-01-01", "2024-01-02")
    assert result1["inserted"] == 2

    result2 = await service.ingest_term("trends_dup", "2024-01-01", "2024-01-02")
    assert result2["inserted"] == 0
    assert result2["total_records"] == 2


@pytest.mark.asyncio
async def test_ingest_api_requires_search_term(client: AsyncClient):
    resp = await client.post("/api/trends/ingest", json={
        "search_term_id": 99999,
        "start_date": "2024-01-01",
        "end_date": "2024-01-02",
    })
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_ingest_api_success(client: AsyncClient):
    df = pd.DataFrame({
        "date": [pd.Timestamp("2024-01-01").date()],
        "interest_score": [15],
    })

    original_fetch = PytrendsProvider.fetch_term
    fake = FakeProvider(data=df)
    PytrendsProvider.fetch_term = fake.fetch_term

    try:
        create_resp = await client.post("/api/search-terms/", json={"term": "api_test", "category": "test"})
        assert create_resp.status_code == 201
        term_id = create_resp.json()["id"]

        resp = await client.post("/api/trends/ingest", json={
            "search_term_id": term_id,
            "start_date": "2024-01-01",
            "end_date": "2024-01-02",
        })
        assert resp.status_code == 200
        body = resp.json()
        assert body["total_inserted"] == 1
        assert len(body["results"]) == 1
    finally:
        PytrendsProvider.fetch_term = original_fetch
