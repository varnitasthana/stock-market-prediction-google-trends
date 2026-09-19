import pytest
import pytest_asyncio
import pandas as pd
import numpy as np
from datetime import date
from decimal import Decimal

from app.services.statistical_analysis_service import StatisticalAnalysisService, StatisticalAnalysisError
from app.schemas.statistics import StatisticsAnalyzeRequest
from app.repositories.features_repo import FeaturesRepository
from app.schemas.features import FeatureGenerateResponse
from app.services.feature_engineering_service import FeatureEngineer

from tests.conftest import client, db_session


def _make_feature_row(symbol, row_date, feature_name, feature_value):
    return {"symbol": symbol, "date": row_date, "feature_name": feature_name, "feature_value": float(feature_value)}


@pytest.mark.asyncio
async def test_descriptive_statistics(client, db_session):
    from app.repositories.search_term_repo import SearchTermRepository
    from app.repositories.market_data_repo import MarketDataRepository
    from app.repositories.trends_repo import TrendsRepository
    from app.schemas.search_terms import SearchTermCreate

    term_repo = SearchTermRepository(db_session)
    term = await term_repo.create(SearchTermCreate(term="desc_term", category="test", active=True))

    market_repo = MarketDataRepository(db_session)
    await market_repo.bulk_insert([
        {"symbol": "DESC", "date": date(2024, 1, 1), "close": 100.0, "volume": 1000},
        {"symbol": "DESC", "date": date(2024, 1, 2), "close": 110.0, "volume": 1100},
        {"symbol": "DESC", "date": date(2024, 1, 3), "close": 105.0, "volume": 1200},
        {"symbol": "DESC", "date": date(2024, 1, 4), "close": 108.0, "volume": 1300},
        {"symbol": "DESC", "date": date(2024, 1, 5), "close": 112.0, "volume": 1400},
        {"symbol": "DESC", "date": date(2024, 1, 8), "close": 115.0, "volume": 1500},
        {"symbol": "DESC", "date": date(2024, 1, 9), "close": 114.0, "volume": 1600},
        {"symbol": "DESC", "date": date(2024, 1, 10), "close": 116.0, "volume": 1700},
        {"symbol": "DESC", "date": date(2024, 1, 11), "close": 118.0, "volume": 1800},
    ])

    trends_repo = TrendsRepository(db_session)
    await trends_repo.bulk_insert([
        {"search_term_id": term.id, "date": date(2024, 1, 1), "interest_score": 10},
        {"search_term_id": term.id, "date": date(2024, 1, 2), "interest_score": 20},
        {"search_term_id": term.id, "date": date(2024, 1, 3), "interest_score": 30},
        {"search_term_id": term.id, "date": date(2024, 1, 4), "interest_score": 40},
        {"search_term_id": term.id, "date": date(2024, 1, 5), "interest_score": 50},
        {"search_term_id": term.id, "date": date(2024, 1, 8), "interest_score": 60},
        {"search_term_id": term.id, "date": date(2024, 1, 9), "interest_score": 70},
        {"search_term_id": term.id, "date": date(2024, 1, 10), "interest_score": 80},
        {"search_term_id": term.id, "date": date(2024, 1, 11), "interest_score": 90},
    ])

    resp = await client.post("/api/features/generate", json={
        "symbol": "DESC",
        "search_term_ids": [term.id],
        "start_date": "2024-01-01",
        "end_date": "2024-01-11",
    })
    assert resp.status_code == 200

    service = StatisticalAnalysisService(db_session)
    result = await service.analyze("DESC", date(2024, 1, 1), date(2024, 1, 11))

    assert result["symbol"] == "DESC"
    assert result["sample_size"] == 3
    assert len(result["descriptive_statistics"]) > 0

    daily_return_stats = next((s for s in result["descriptive_statistics"] if s["feature"] == "daily_return"), None)
    assert daily_return_stats is not None
    assert daily_return_stats["count"] == 3
    assert daily_return_stats["min"] <= daily_return_stats["mean"] <= daily_return_stats["max"]


@pytest.mark.asyncio
async def test_correlation_values_within_range(client, db_session):
    from app.repositories.search_term_repo import SearchTermRepository
    from app.repositories.market_data_repo import MarketDataRepository
    from app.repositories.trends_repo import TrendsRepository
    from app.schemas.search_terms import SearchTermCreate

    term_repo = SearchTermRepository(db_session)
    term = await term_repo.create(SearchTermCreate(term="corr_term", category="test", active=True))

    market_repo = MarketDataRepository(db_session)
    await market_repo.bulk_insert([
        {"symbol": "CORR", "date": date(2024, 1, 1), "close": 100.0, "volume": 1000},
        {"symbol": "CORR", "date": date(2024, 1, 2), "close": 110.0, "volume": 1100},
        {"symbol": "CORR", "date": date(2024, 1, 3), "close": 105.0, "volume": 1200},
        {"symbol": "CORR", "date": date(2024, 1, 4), "close": 108.0, "volume": 1300},
        {"symbol": "CORR", "date": date(2024, 1, 5), "close": 112.0, "volume": 1400},
        {"symbol": "CORR", "date": date(2024, 1, 8), "close": 115.0, "volume": 1500},
        {"symbol": "CORR", "date": date(2024, 1, 9), "close": 114.0, "volume": 1600},
        {"symbol": "CORR", "date": date(2024, 1, 10), "close": 116.0, "volume": 1700},
        {"symbol": "CORR", "date": date(2024, 1, 11), "close": 118.0, "volume": 1800},
    ])

    trends_repo = TrendsRepository(db_session)
    await trends_repo.bulk_insert([
        {"search_term_id": term.id, "date": date(2024, 1, 1), "interest_score": 10},
        {"search_term_id": term.id, "date": date(2024, 1, 2), "interest_score": 20},
        {"search_term_id": term.id, "date": date(2024, 1, 3), "interest_score": 30},
        {"search_term_id": term.id, "date": date(2024, 1, 4), "interest_score": 40},
        {"search_term_id": term.id, "date": date(2024, 1, 5), "interest_score": 50},
        {"search_term_id": term.id, "date": date(2024, 1, 8), "interest_score": 60},
        {"search_term_id": term.id, "date": date(2024, 1, 9), "interest_score": 70},
        {"search_term_id": term.id, "date": date(2024, 1, 10), "interest_score": 80},
        {"search_term_id": term.id, "date": date(2024, 1, 11), "interest_score": 90},
    ])

    resp = await client.post("/api/features/generate", json={
        "symbol": "CORR",
        "search_term_ids": [term.id],
        "start_date": "2024-01-01",
        "end_date": "2024-01-11",
    })
    assert resp.status_code == 200

    service = StatisticalAnalysisService(db_session)
    result = await service.analyze("CORR", date(2024, 1, 1), date(2024, 1, 11))

    assert len(result["correlations"]) > 0
    for corr in result["correlations"]:
        assert -1.0 <= corr["correlation"] <= 1.0
        assert 0.0 <= corr["p_value"] <= 1.0
        assert corr["sample_size"] >= 3


@pytest.mark.asyncio
async def test_multiple_search_terms_analysis(client, db_session):
    from app.repositories.search_term_repo import SearchTermRepository
    from app.repositories.market_data_repo import MarketDataRepository
    from app.repositories.trends_repo import TrendsRepository
    from app.schemas.search_terms import SearchTermCreate

    term_repo = SearchTermRepository(db_session)
    term_a = await term_repo.create(SearchTermCreate(term="term_a", category="test", active=True))
    term_b = await term_repo.create(SearchTermCreate(term="term_b", category="test", active=True))

    market_repo = MarketDataRepository(db_session)
    await market_repo.bulk_insert([
        {"symbol": "MSTAT", "date": date(2024, 1, 1), "close": 100.0, "volume": 1000},
        {"symbol": "MSTAT", "date": date(2024, 1, 2), "close": 110.0, "volume": 1100},
        {"symbol": "MSTAT", "date": date(2024, 1, 3), "close": 105.0, "volume": 1200},
        {"symbol": "MSTAT", "date": date(2024, 1, 4), "close": 108.0, "volume": 1300},
        {"symbol": "MSTAT", "date": date(2024, 1, 5), "close": 112.0, "volume": 1400},
        {"symbol": "MSTAT", "date": date(2024, 1, 8), "close": 115.0, "volume": 1500},
        {"symbol": "MSTAT", "date": date(2024, 1, 9), "close": 114.0, "volume": 1600},
        {"symbol": "MSTAT", "date": date(2024, 1, 10), "close": 116.0, "volume": 1700},
        {"symbol": "MSTAT", "date": date(2024, 1, 11), "close": 118.0, "volume": 1800},
    ])

    trends_repo = TrendsRepository(db_session)
    await trends_repo.bulk_insert([
        {"search_term_id": term_a.id, "date": date(2024, 1, 1), "interest_score": 10},
        {"search_term_id": term_a.id, "date": date(2024, 1, 2), "interest_score": 20},
        {"search_term_id": term_a.id, "date": date(2024, 1, 3), "interest_score": 30},
        {"search_term_id": term_a.id, "date": date(2024, 1, 4), "interest_score": 40},
        {"search_term_id": term_a.id, "date": date(2024, 1, 5), "interest_score": 50},
        {"search_term_id": term_a.id, "date": date(2024, 1, 8), "interest_score": 60},
        {"search_term_id": term_a.id, "date": date(2024, 1, 9), "interest_score": 70},
        {"search_term_id": term_a.id, "date": date(2024, 1, 10), "interest_score": 80},
        {"search_term_id": term_a.id, "date": date(2024, 1, 11), "interest_score": 90},
    ])
    await trends_repo.bulk_insert([
        {"search_term_id": term_b.id, "date": date(2024, 1, 1), "interest_score": 5},
        {"search_term_id": term_b.id, "date": date(2024, 1, 2), "interest_score": 15},
        {"search_term_id": term_b.id, "date": date(2024, 1, 3), "interest_score": 25},
        {"search_term_id": term_b.id, "date": date(2024, 1, 4), "interest_score": 35},
        {"search_term_id": term_b.id, "date": date(2024, 1, 5), "interest_score": 45},
        {"search_term_id": term_b.id, "date": date(2024, 1, 8), "interest_score": 55},
        {"search_term_id": term_b.id, "date": date(2024, 1, 9), "interest_score": 65},
        {"search_term_id": term_b.id, "date": date(2024, 1, 10), "interest_score": 75},
        {"search_term_id": term_b.id, "date": date(2024, 1, 11), "interest_score": 85},
    ])

    resp = await client.post("/api/features/generate", json={
        "symbol": "MSTAT",
        "search_term_ids": [term_a.id, term_b.id],
        "start_date": "2024-01-01",
        "end_date": "2024-01-11",
    })
    assert resp.status_code == 200

    service = StatisticalAnalysisService(db_session)
    result = await service.analyze("MSTAT", date(2024, 1, 1), date(2024, 1, 11))

    assert result["sample_size"] == 3
    trend_features = [c for c in result.get("descriptive_statistics", []) if "trend" in c.get("feature", "")]

    assert len(result["correlations"]) > 0
    features_in_corr = {c["feature"] for c in result["correlations"]}
    assert "term_a_trend" in features_in_corr
    assert "term_b_trend" in features_in_corr

    assert "direction_0" in result["direction_analysis"]
    assert "direction_1" in result["direction_analysis"]


@pytest.mark.asyncio
async def test_lag_analysis(client, db_session):
    from app.repositories.search_term_repo import SearchTermRepository
    from app.repositories.market_data_repo import MarketDataRepository
    from app.repositories.trends_repo import TrendsRepository
    from app.schemas.search_terms import SearchTermCreate

    term_repo = SearchTermRepository(db_session)
    term = await term_repo.create(SearchTermCreate(term="lag_term", category="test", active=True))

    market_repo = MarketDataRepository(db_session)
    await market_repo.bulk_insert([
        {"symbol": "LAG", "date": date(2024, 1, 1), "close": 100.0, "volume": 1000},
        {"symbol": "LAG", "date": date(2024, 1, 2), "close": 110.0, "volume": 1100},
        {"symbol": "LAG", "date": date(2024, 1, 3), "close": 105.0, "volume": 1200},
        {"symbol": "LAG", "date": date(2024, 1, 4), "close": 108.0, "volume": 1300},
        {"symbol": "LAG", "date": date(2024, 1, 5), "close": 112.0, "volume": 1400},
        {"symbol": "LAG", "date": date(2024, 1, 8), "close": 115.0, "volume": 1500},
        {"symbol": "LAG", "date": date(2024, 1, 9), "close": 114.0, "volume": 1600},
        {"symbol": "LAG", "date": date(2024, 1, 10), "close": 116.0, "volume": 1700},
        {"symbol": "LAG", "date": date(2024, 1, 11), "close": 118.0, "volume": 1800},
    ])

    trends_repo = TrendsRepository(db_session)
    await trends_repo.bulk_insert([
        {"search_term_id": term.id, "date": date(2024, 1, 1), "interest_score": 10},
        {"search_term_id": term.id, "date": date(2024, 1, 2), "interest_score": 20},
        {"search_term_id": term.id, "date": date(2024, 1, 3), "interest_score": 30},
        {"search_term_id": term.id, "date": date(2024, 1, 4), "interest_score": 40},
        {"search_term_id": term.id, "date": date(2024, 1, 5), "interest_score": 50},
        {"search_term_id": term.id, "date": date(2024, 1, 8), "interest_score": 60},
        {"search_term_id": term.id, "date": date(2024, 1, 9), "interest_score": 70},
        {"search_term_id": term.id, "date": date(2024, 1, 10), "interest_score": 80},
        {"search_term_id": term.id, "date": date(2024, 1, 11), "interest_score": 90},
    ])

    resp = await client.post("/api/features/generate", json={
        "symbol": "LAG",
        "search_term_ids": [term.id],
        "start_date": "2024-01-01",
        "end_date": "2024-01-11",
    })
    assert resp.status_code == 200

    service = StatisticalAnalysisService(db_session)
    result = await service.analyze("LAG", date(2024, 1, 1), date(2024, 1, 11))

    assert len(result["lag_analysis"]) > 0
    lag_features = [r["feature"] for r in result["lag_analysis"]]
    assert "lag_term_trend_lag_1" in lag_features
    assert "lag_term_trend_lag_3" in lag_features
    if "lag_term_trend_lag_7" in lag_features:
        for r in result["lag_analysis"]:
            assert r["feature"] == "lag_term_trend_lag_7"
            assert -1.0 <= r["correlation"] <= 1.0
            assert 0.0 <= r["p_value"] <= 1.0


@pytest.mark.asyncio
async def test_direction_analysis(client, db_session):
    from app.repositories.search_term_repo import SearchTermRepository
    from app.repositories.market_data_repo import MarketDataRepository
    from app.repositories.trends_repo import TrendsRepository
    from app.schemas.search_terms import SearchTermCreate

    term_repo = SearchTermRepository(db_session)
    term = await term_repo.create(SearchTermCreate(term="dir_term", category="test", active=True))

    market_repo = MarketDataRepository(db_session)
    await market_repo.bulk_insert([
        {"symbol": "DIR", "date": date(2024, 1, 1), "close": 100.0, "volume": 1000},
        {"symbol": "DIR", "date": date(2024, 1, 2), "close": 110.0, "volume": 1100},
        {"symbol": "DIR", "date": date(2024, 1, 3), "close": 105.0, "volume": 1200},
        {"symbol": "DIR", "date": date(2024, 1, 4), "close": 108.0, "volume": 1300},
        {"symbol": "DIR", "date": date(2024, 1, 5), "close": 112.0, "volume": 1400},
        {"symbol": "DIR", "date": date(2024, 1, 8), "close": 115.0, "volume": 1500},
        {"symbol": "DIR", "date": date(2024, 1, 9), "close": 114.0, "volume": 1600},
        {"symbol": "DIR", "date": date(2024, 1, 10), "close": 116.0, "volume": 1700},
        {"symbol": "DIR", "date": date(2024, 1, 11), "close": 118.0, "volume": 1800},
    ])

    trends_repo = TrendsRepository(db_session)
    await trends_repo.bulk_insert([
        {"search_term_id": term.id, "date": date(2024, 1, 1), "interest_score": 10},
        {"search_term_id": term.id, "date": date(2024, 1, 2), "interest_score": 20},
        {"search_term_id": term.id, "date": date(2024, 1, 3), "interest_score": 30},
        {"search_term_id": term.id, "date": date(2024, 1, 4), "interest_score": 40},
        {"search_term_id": term.id, "date": date(2024, 1, 5), "interest_score": 50},
        {"search_term_id": term.id, "date": date(2024, 1, 8), "interest_score": 60},
        {"search_term_id": term.id, "date": date(2024, 1, 9), "interest_score": 70},
        {"search_term_id": term.id, "date": date(2024, 1, 10), "interest_score": 80},
        {"search_term_id": term.id, "date": date(2024, 1, 11), "interest_score": 90},
    ])

    resp = await client.post("/api/features/generate", json={
        "symbol": "DIR",
        "search_term_ids": [term.id],
        "start_date": "2024-01-01",
        "end_date": "2024-01-11",
    })
    assert resp.status_code == 200

    service = StatisticalAnalysisService(db_session)
    result = await service.analyze("DIR", date(2024, 1, 1), date(2024, 1, 11))

    assert "direction_0" in result["direction_analysis"]
    assert "direction_1" in result["direction_analysis"]
    dir_0 = result["direction_analysis"]["direction_0"]
    dir_1 = result["direction_analysis"]["direction_1"]
    assert len(dir_0) > 0
    assert len(dir_1) > 0
    features_0 = {s["feature"] for s in dir_0}
    features_1 = {s["feature"] for s in dir_1}
    assert "dir_term_trend" in features_0
    assert "dir_term_trend" in features_1


@pytest.mark.asyncio
async def test_statistics_empty_dataset(client, db_session):
    service = StatisticalAnalysisService(db_session)
    with pytest.raises(StatisticalAnalysisError):
        await service.analyze("NONEXISTENT", date(2024, 1, 1), date(2024, 1, 5))


@pytest.mark.asyncio
async def test_statistics_api_success(client, db_session):
    from app.repositories.search_term_repo import SearchTermRepository
    from app.repositories.market_data_repo import MarketDataRepository
    from app.repositories.trends_repo import TrendsRepository
    from app.schemas.search_terms import SearchTermCreate

    term_repo = SearchTermRepository(db_session)
    term = await term_repo.create(SearchTermCreate(term="api_term", category="test", active=True))

    market_repo = MarketDataRepository(db_session)
    await market_repo.bulk_insert([
        {"symbol": "APISTAT", "date": date(2024, 1, 1), "close": 100.0, "volume": 1000},
        {"symbol": "APISTAT", "date": date(2024, 1, 2), "close": 110.0, "volume": 1100},
        {"symbol": "APISTAT", "date": date(2024, 1, 3), "close": 105.0, "volume": 1200},
        {"symbol": "APISTAT", "date": date(2024, 1, 4), "close": 108.0, "volume": 1300},
        {"symbol": "APISTAT", "date": date(2024, 1, 5), "close": 112.0, "volume": 1400},
        {"symbol": "APISTAT", "date": date(2024, 1, 8), "close": 115.0, "volume": 1500},
        {"symbol": "APISTAT", "date": date(2024, 1, 9), "close": 114.0, "volume": 1600},
        {"symbol": "APISTAT", "date": date(2024, 1, 10), "close": 116.0, "volume": 1700},
        {"symbol": "APISTAT", "date": date(2024, 1, 11), "close": 118.0, "volume": 1800},
    ])

    trends_repo = TrendsRepository(db_session)
    await trends_repo.bulk_insert([
        {"search_term_id": term.id, "date": date(2024, 1, 1), "interest_score": 10},
        {"search_term_id": term.id, "date": date(2024, 1, 2), "interest_score": 20},
        {"search_term_id": term.id, "date": date(2024, 1, 3), "interest_score": 30},
        {"search_term_id": term.id, "date": date(2024, 1, 4), "interest_score": 40},
        {"search_term_id": term.id, "date": date(2024, 1, 5), "interest_score": 50},
        {"search_term_id": term.id, "date": date(2024, 1, 8), "interest_score": 60},
        {"search_term_id": term.id, "date": date(2024, 1, 9), "interest_score": 70},
        {"search_term_id": term.id, "date": date(2024, 1, 10), "interest_score": 80},
        {"search_term_id": term.id, "date": date(2024, 1, 11), "interest_score": 90},
    ])

    resp = await client.post("/api/features/generate", json={
        "symbol": "APISTAT",
        "search_term_ids": [term.id],
        "start_date": "2024-01-01",
        "end_date": "2024-01-11",
    })
    assert resp.status_code == 200

    resp = await client.post("/api/statistics/analyze", json={
        "symbol": "APISTAT",
        "start_date": "2024-01-01",
        "end_date": "2024-01-11",
    })
    assert resp.status_code == 200
    body = resp.json()
    assert body["symbol"] == "APISTAT"
    assert body["sample_size"] == 3
    assert len(body["descriptive_statistics"]) > 0
    assert len(body["correlations"]) > 0
    assert len(body["lag_analysis"]) > 0
    assert "direction_0" in body["direction_analysis"]
    assert "direction_1" in body["direction_analysis"]


@pytest.mark.asyncio
async def test_statistics_api_no_features(client, db_session):
    resp = await client.post("/api/statistics/analyze", json={
        "symbol": "NONEXISTENT",
        "start_date": "2024-01-01",
        "end_date": "2024-01-05",
    })
    assert resp.status_code == 400
