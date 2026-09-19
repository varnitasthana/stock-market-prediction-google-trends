from datetime import date

import pandas as pd
import pytest
from httpx import AsyncClient

from app.services.alignment_service import AlignmentService
from app.utils.validators import validate_market_data, validate_trends_data


def test_validate_market_data_valid():
    df = pd.DataFrame({
        "date": [date(2024, 1, 1), date(2024, 1, 2)],
        "open": [100.0, 101.0],
        "high": [105.0, 106.0],
        "low": [99.0, 100.0],
        "close": [104.0, 105.0],
        "adj_close": [104.0, 105.0],
        "volume": [1000, 1100],
    })
    result = validate_market_data(df, "TEST")
    assert len(result) == 2
    assert result["date"].tolist() == [date(2024, 1, 1), date(2024, 1, 2)]


def test_validate_market_data_drops_duplicates():
    df = pd.DataFrame({
        "date": [date(2024, 1, 1), date(2024, 1, 1)],
        "open": [100.0, 101.0],
        "high": [105.0, 106.0],
        "low": [99.0, 100.0],
        "close": [104.0, 105.0],
        "adj_close": [104.0, 105.0],
        "volume": [1000, 1100],
    })
    result = validate_market_data(df, "TEST")
    assert len(result) == 1


def test_validate_market_data_invalid_ohlc():
    df = pd.DataFrame({
        "date": [date(2024, 1, 1)],
        "open": [100.0],
        "high": [99.0],
        "low": [101.0],
        "close": [105.0],
        "adj_close": [104.0],
        "volume": [1000],
    })
    result = validate_market_data(df, "TEST")
    assert len(result) == 1


def test_validate_trends_data_valid():
    df = pd.DataFrame({
        "date": [date(2024, 1, 1), date(2024, 1, 2)],
        "interest_score": [50, 100],
    })
    result = validate_trends_data(df)
    assert len(result) == 2
    assert result["interest_score"].tolist() == [50, 100]


def test_validate_trends_data_preserves_zero():
    df = pd.DataFrame({
        "date": [date(2024, 1, 1)],
        "interest_score": [0],
    })
    result = validate_trends_data(df)
    assert len(result) == 1
    assert result["interest_score"].tolist() == [0]


def test_validate_trends_data_out_of_range():
    df = pd.DataFrame({
        "date": [date(2024, 1, 1), date(2024, 1, 2)],
        "interest_score": [-5, 150],
    })
    result = validate_trends_data(df)
    assert len(result) == 2


@pytest.mark.asyncio
async def test_alignment_partial_overlap(client: AsyncClient, db_session):
    await client.post("/api/search-terms/", json={"term": "align_test", "category": "test"})
    term = await client.get("/api/search-terms/?active_only=false")
    term_id = term.json()[0]["id"]

    from app.repositories.market_data_repo import MarketDataRepository

    market_repo = MarketDataRepository(db_session)
    await market_repo.bulk_insert([
        {"symbol": "ALIGN", "date": date(2024, 1, 1), "close": 100.0, "volume": 1000},
        {"symbol": "ALIGN", "date": date(2024, 1, 2), "close": 101.0, "volume": 1100},
        {"symbol": "ALIGN", "date": date(2024, 1, 3), "close": 102.0, "volume": 1200},
        {"symbol": "ALIGN", "date": date(2024, 1, 4), "close": 103.0, "volume": 1300},
        {"symbol": "ALIGN", "date": date(2024, 1, 5), "close": 104.0, "volume": 1400},
    ])

    from app.repositories.trends_repo import TrendsRepository
    trends_repo = TrendsRepository(db_session)
    await trends_repo.bulk_insert([
        {"search_term_id": term_id, "date": date(2024, 1, 1), "interest_score": 10},
        {"search_term_id": term_id, "date": date(2024, 1, 2), "interest_score": 20},
        {"search_term_id": term_id, "date": date(2024, 1, 4), "interest_score": 40},
        {"search_term_id": term_id, "date": date(2024, 1, 5), "interest_score": 50},
    ])

    service = AlignmentService(db_session)
    result = await service.align("ALIGN", term_id, date(2024, 1, 1), date(2024, 1, 5))

    assert len(result["rows"]) == 4
    dates = [r.date for r in result["rows"]]
    assert dates == [date(2024, 1, 1), date(2024, 1, 2), date(2024, 1, 4), date(2024, 1, 5)]
    assert result["quality"].unmatched_market_dates == [date(2024, 1, 3)]
    assert result["quality"].unmatched_trends_dates == []
    assert result["quality"].aligned_rows == 4


@pytest.mark.asyncio
async def test_alignment_empty_market(client: AsyncClient, db_session):
    await client.post("/api/search-terms/", json={"term": "align_empty", "category": "test"})
    term = await client.get("/api/search-terms/?active_only=false")
    term_id = term.json()[0]["id"]

    from app.repositories.trends_repo import TrendsRepository

    trends_repo = TrendsRepository(db_session)
    await trends_repo.bulk_insert([
        {"search_term_id": term_id, "date": date(2024, 1, 1), "interest_score": 10},
    ])

    service = AlignmentService(db_session)
    result = await service.align("EMPTY", term_id, date(2024, 1, 1), date(2024, 1, 1))

    assert len(result["rows"]) == 0
    assert result["quality"].aligned_rows == 0
    assert result["quality"].unmatched_trends_dates == [date(2024, 1, 1)]


@pytest.mark.asyncio
async def test_alignment_api_endpoint(client: AsyncClient, db_session):
    await client.post("/api/search-terms/", json={"term": "align_api", "category": "test"})
    term = await client.get("/api/search-terms/?active_only=false")
    term_id = term.json()[0]["id"]

    from app.repositories.market_data_repo import MarketDataRepository
    from app.repositories.trends_repo import TrendsRepository

    market_repo = MarketDataRepository(db_session)
    await market_repo.bulk_insert([
        {"symbol": "API", "date": date(2024, 1, 1), "close": 100.0, "volume": 1000},
        {"symbol": "API", "date": date(2024, 1, 2), "close": 101.0, "volume": 1100},
    ])

    trends_repo = TrendsRepository(db_session)
    await trends_repo.bulk_insert([
        {"search_term_id": term_id, "date": date(2024, 1, 1), "interest_score": 10},
        {"search_term_id": term_id, "date": date(2024, 1, 2), "interest_score": 20},
    ])

    resp = await client.post("/api/alignment/", json={
        "symbol": "API",
        "search_term_id": term_id,
        "start_date": "2024-01-01",
        "end_date": "2024-01-02",
    })
    assert resp.status_code == 200
    body = resp.json()
    assert body["symbol"] == "API"
    assert len(body["rows"]) == 2
    assert body["rows"][0]["interest_score"] == 10
    assert body["quality"]["aligned_rows"] == 2