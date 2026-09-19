import pytest
import pytest_asyncio
import pandas as pd
import numpy as np
from datetime import date
from decimal import Decimal

from app.services.feature_engineering_service import FeatureEngineer, FeatureEngineeringError
from app.schemas.features import FeatureGenerateRequest, FeatureGenerateResponse
from app.schemas.search_terms import SearchTermCreate
from app.utils.validators import validate_market_data

from tests.conftest import client, db_session


def _build_market_df(prices: list[tuple[date, float]]) -> pd.DataFrame:
    rows = []
    for d, close in prices:
        rows.append({"date": d, "close": close, "open": close, "high": close, "low": close, "volume": 1000})
    return pd.DataFrame(rows)


def test_calculate_returns():
    df = _build_market_df([
        (date(2024, 1, 1), 100.0),
        (date(2024, 1, 2), 110.0),
        (date(2024, 1, 3), 105.0),
    ])
    returns = FeatureEngineer._calculate_returns(df["close"])
    assert np.isclose(returns.iloc[1], 0.10)
    assert np.isclose(returns.iloc[2], -0.045454545454545414, atol=1e-6)


def test_calculate_log_returns():
    df = _build_market_df([
        (date(2024, 1, 1), 100.0),
        (date(2024, 1, 2), 110.0),
    ])
    log_returns = FeatureEngineer._calculate_log_returns(df["close"])
    assert np.isclose(log_returns.iloc[1], np.log(1.10))


def test_rolling_volatility():
    df = _build_market_df([
        (date(2024, 1, 1), 100.0),
        (date(2024, 1, 2), 110.0),
        (date(2024, 1, 3), 105.0),
        (date(2024, 1, 4), 108.0),
        (date(2024, 1, 5), 112.0),
    ])
    returns = FeatureEngineer._calculate_returns(df["close"])
    vol = FeatureEngineer._calculate_rolling_volatility(returns, window=3)
    assert vol.iloc[2] is not None
    assert vol.iloc[4] is not None


def test_sanitize_term():
    assert FeatureEngineer._sanitize_term("NIFTY 50") == "nifty_50"
    assert FeatureEngineer._sanitize_term("Interest Rates") == "interest_rates"


def test_merge_trends_to_market():
    market_dates = pd.Series([date(2024, 1, 1), date(2024, 1, 2), date(2024, 1, 3)])
    trends_df = pd.DataFrame({
        "date": [date(2024, 1, 1), date(2024, 1, 3)],
        "interest_score": [10, 30],
    })
    merged = FeatureEngineer._merge_trends_to_market(market_dates, trends_df)
    assert merged.iloc[0] == 10
    assert pd.isna(merged.iloc[1])
    assert merged.iloc[2] == 30


@pytest.mark.asyncio
async def test_generate_features_end_to_end(client, db_session):
    from app.repositories.market_data_repo import MarketDataRepository
    from app.repositories.trends_repo import TrendsRepository
    from app.repositories.search_term_repo import SearchTermRepository

    term_repo = SearchTermRepository(db_session)
    term = await term_repo.create(SearchTermCreate(term="recession", category="macro", active=True))

    market_repo = MarketDataRepository(db_session)
    await market_repo.bulk_insert([
        {"symbol": "NSEI", "date": date(2024, 1, 1), "close": 100.0, "volume": 1000},
        {"symbol": "NSEI", "date": date(2024, 1, 2), "close": 110.0, "volume": 1100},
        {"symbol": "NSEI", "date": date(2024, 1, 3), "close": 105.0, "volume": 1200},
        {"symbol": "NSEI", "date": date(2024, 1, 4), "close": 108.0, "volume": 1300},
        {"symbol": "NSEI", "date": date(2024, 1, 5), "close": 112.0, "volume": 1400},
        {"symbol": "NSEI", "date": date(2024, 1, 8), "close": 115.0, "volume": 1500},
        {"symbol": "NSEI", "date": date(2024, 1, 9), "close": 114.0, "volume": 1600},
        {"symbol": "NSEI", "date": date(2024, 1, 10), "close": 116.0, "volume": 1700},
        {"symbol": "NSEI", "date": date(2024, 1, 11), "close": 118.0, "volume": 1800},
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

    engineer = FeatureEngineer(db_session)
    result = await engineer.generate_features(
        symbol="NSEI",
        search_term_ids=[term.id],
        start_date=date(2024, 1, 1),
        end_date=date(2024, 1, 11),
        persist=True,
    )

    assert result["symbol"] == "NSEI"
    assert result["rows_generated"] == 3
    assert result["rows_persisted"] > 0
    assert "recession_trend" in result["features_generated"]
    assert "return_lag_1" in result["features_generated"]
    assert "next_day_return" in result["features_generated"]
    assert "next_day_direction" in result["features_generated"]


@pytest.mark.asyncio
async def test_generate_features_api(client, db_session):
    from app.repositories.market_data_repo import MarketDataRepository
    from app.repositories.trends_repo import TrendsRepository
    from app.repositories.search_term_repo import SearchTermRepository

    term_repo = SearchTermRepository(db_session)
    term = await term_repo.create(SearchTermCreate(term="inflation", category="macro", active=True))

    market_repo = MarketDataRepository(db_session)
    await market_repo.bulk_insert([
        {"symbol": "NSEI", "date": date(2024, 1, 1), "close": 100.0, "volume": 1000},
        {"symbol": "NSEI", "date": date(2024, 1, 2), "close": 110.0, "volume": 1100},
        {"symbol": "NSEI", "date": date(2024, 1, 3), "close": 105.0, "volume": 1200},
        {"symbol": "NSEI", "date": date(2024, 1, 4), "close": 108.0, "volume": 1300},
        {"symbol": "NSEI", "date": date(2024, 1, 5), "close": 112.0, "volume": 1400},
        {"symbol": "NSEI", "date": date(2024, 1, 8), "close": 115.0, "volume": 1500},
        {"symbol": "NSEI", "date": date(2024, 1, 9), "close": 114.0, "volume": 1600},
        {"symbol": "NSEI", "date": date(2024, 1, 10), "close": 116.0, "volume": 1700},
        {"symbol": "NSEI", "date": date(2024, 1, 11), "close": 118.0, "volume": 1800},
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
        "symbol": "NSEI",
        "search_term_ids": [term.id],
        "start_date": "2024-01-01",
        "end_date": "2024-01-11",
    })
    assert resp.status_code == 200
    body = resp.json()
    assert body["symbol"] == "NSEI"
    assert body["rows_generated"] == 3
    assert "inflation_trend" in body["features_generated"]


@pytest.mark.asyncio
async def test_generate_features_no_market_data(client, db_session):
    resp = await client.post("/api/features/generate", json={
        "symbol": "EMPTY",
        "search_term_ids": [1],
        "start_date": "2024-01-01",
        "end_date": "2024-01-05",
    })
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_generate_features_idempotent(client, db_session):
    from app.repositories.market_data_repo import MarketDataRepository
    from app.repositories.trends_repo import TrendsRepository
    from app.repositories.search_term_repo import SearchTermRepository

    term_repo = SearchTermRepository(db_session)
    term = await term_repo.create(SearchTermCreate(term="idempotent", category="test", active=True))

    market_repo = MarketDataRepository(db_session)
    await market_repo.bulk_insert([
        {"symbol": "IDEM", "date": date(2024, 1, 1), "close": 100.0, "volume": 1000},
        {"symbol": "IDEM", "date": date(2024, 1, 2), "close": 110.0, "volume": 1100},
        {"symbol": "IDEM", "date": date(2024, 1, 3), "close": 105.0, "volume": 1200},
        {"symbol": "IDEM", "date": date(2024, 1, 4), "close": 108.0, "volume": 1300},
        {"symbol": "IDEM", "date": date(2024, 1, 5), "close": 112.0, "volume": 1400},
        {"symbol": "IDEM", "date": date(2024, 1, 8), "close": 115.0, "volume": 1500},
        {"symbol": "IDEM", "date": date(2024, 1, 9), "close": 114.0, "volume": 1600},
        {"symbol": "IDEM", "date": date(2024, 1, 10), "close": 116.0, "volume": 1700},
        {"symbol": "IDEM", "date": date(2024, 1, 11), "close": 118.0, "volume": 1800},
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

    resp1 = await client.post("/api/features/generate", json={
        "symbol": "IDEM",
        "search_term_ids": [term.id],
        "start_date": "2024-01-01",
        "end_date": "2024-01-11",
    })
    assert resp1.status_code == 200

    resp2 = await client.post("/api/features/generate", json={
        "symbol": "IDEM",
        "search_term_ids": [term.id],
        "start_date": "2024-01-01",
        "end_date": "2024-01-11",
    })
    assert resp2.status_code == 200

    from app.repositories.features_repo import FeaturesRepository
    features_repo = FeaturesRepository(db_session)
    all_features = await features_repo.get_by_symbol_and_date_range("IDEM", date(2024, 1, 1), date(2024, 1, 5))

    feature_records = [(f.date, f.feature_name) for f in all_features]
    assert len(feature_records) == len(set(feature_records)), "Duplicate features found"


@pytest.mark.asyncio
async def test_generate_features_multiple_terms(client, db_session):
    from app.repositories.market_data_repo import MarketDataRepository
    from app.repositories.trends_repo import TrendsRepository
    from app.repositories.search_term_repo import SearchTermRepository

    term_repo = SearchTermRepository(db_session)
    term_a = await term_repo.create(SearchTermCreate(term="recession", category="macro", active=True))
    term_b = await term_repo.create(SearchTermCreate(term="inflation", category="macro", active=True))

    market_repo = MarketDataRepository(db_session)
    await market_repo.bulk_insert([
        {"symbol": "MULTI", "date": date(2024, 1, 1), "close": 100.0, "volume": 1000},
        {"symbol": "MULTI", "date": date(2024, 1, 2), "close": 110.0, "volume": 1100},
        {"symbol": "MULTI", "date": date(2024, 1, 3), "close": 105.0, "volume": 1200},
        {"symbol": "MULTI", "date": date(2024, 1, 4), "close": 108.0, "volume": 1300},
        {"symbol": "MULTI", "date": date(2024, 1, 5), "close": 112.0, "volume": 1400},
        {"symbol": "MULTI", "date": date(2024, 1, 8), "close": 115.0, "volume": 1500},
        {"symbol": "MULTI", "date": date(2024, 1, 9), "close": 114.0, "volume": 1600},
        {"symbol": "MULTI", "date": date(2024, 1, 10), "close": 116.0, "volume": 1700},
        {"symbol": "MULTI", "date": date(2024, 1, 11), "close": 118.0, "volume": 1800},
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
        "symbol": "MULTI",
        "search_term_ids": [term_a.id, term_b.id],
        "start_date": "2024-01-01",
        "end_date": "2024-01-11",
    })
    assert resp.status_code == 200
    body = resp.json()
    assert body["symbol"] == "MULTI"
    assert body["rows_generated"] == 3
    assert "recession_trend" in body["features_generated"]
    assert "inflation_trend" in body["features_generated"]


@pytest.mark.asyncio
async def test_generate_features_no_nan_inf(client, db_session):
    from app.repositories.market_data_repo import MarketDataRepository
    from app.repositories.trends_repo import TrendsRepository
    from app.repositories.search_term_repo import SearchTermRepository

    term_repo = SearchTermRepository(db_session)
    term = await term_repo.create(SearchTermCreate(term="clean", category="test", active=True))

    market_repo = MarketDataRepository(db_session)
    closes = [100.0 + i * 2.0 for i in range(15)]
    market_records = [
        {"symbol": "CLEAN", "date": date(2024, 1, 1) + __import__("datetime").timedelta(days=i), "close": closes[i], "volume": 1000 + i}
        for i in range(15)
    ]
    await market_repo.bulk_insert(market_records)

    trends_repo = TrendsRepository(db_session)
    trends_records = [
        {"search_term_id": term.id, "date": date(2024, 1, 1) + __import__("datetime").timedelta(days=i), "interest_score": 10 + i * 5}
        for i in range(15)
    ]
    await trends_repo.bulk_insert(trends_records)

    resp = await client.post("/api/features/generate", json={
        "symbol": "CLEAN",
        "search_term_ids": [term.id],
        "start_date": "2024-01-01",
        "end_date": "2024-01-15",
    })
    assert resp.status_code == 200

    from app.repositories.features_repo import FeaturesRepository
    features_repo = FeaturesRepository(db_session)
    all_features = await features_repo.get_by_symbol_and_date_range("CLEAN", date(2024, 1, 1), date(2024, 1, 15))
    for f in all_features:
        assert f.feature_value is not None
        val = float(f.feature_value)
        assert not __import__("numpy").isnan(val)
        assert not __import__("numpy").isinf(val)


def test_generate_features_target_values():
    from app.services.feature_engineering_service import FeatureEngineer

    df = pd.DataFrame({
        "date": [date(2024, 1, 1), date(2024, 1, 2), date(2024, 1, 3), date(2024, 1, 4), date(2024, 1, 5), date(2024, 1, 8)],
        "close": [100.0, 110.0, 105.0, 108.0, 112.0, 109.0],
        "open": [100.0, 110.0, 105.0, 108.0, 112.0, 109.0],
        "high": [100.0, 110.0, 105.0, 108.0, 112.0, 109.0],
        "low": [100.0, 110.0, 105.0, 108.0, 112.0, 109.0],
        "volume": [1000, 1100, 1200, 1300, 1400, 1500],
    })

    engineer = FeatureEngineer.__new__(FeatureEngineer)
    result = engineer._market_to_df([
        type("Row", (), {"date": r["date"], "open": r["open"], "high": r["high"], "low": r["low"], "close": r["close"], "adj_close": r["close"], "volume": r["volume"]})()
        for r in df.to_dict("records")
    ])
    result = validate_market_data(result, "TGT")
    result["daily_return"] = engineer._calculate_returns(result["close"])
    result["volatility_5d"] = engineer._calculate_rolling_volatility(result["daily_return"], window=3)
    result["next_day_return"] = result["daily_return"].shift(-1)
    result["next_day_direction"] = (result["next_day_return"] > 0).astype(int)

    valid = result.dropna(subset=["daily_return", "volatility_5d", "next_day_return"]).reset_index(drop=True)

    assert len(valid) >= 2
    first = valid.loc[0]
    assert first["next_day_direction"] == 1
    assert np.isclose(first["next_day_return"], (112.0 / 108.0) - 1)
    last = valid.loc[len(valid) - 1]
    assert last["next_day_direction"] == 0
    assert np.isclose(last["next_day_return"], (109.0 / 112.0) - 1)


def test_generate_features_leakage_prevention():
    from app.services.feature_engineering_service import FeatureEngineer

    df = pd.DataFrame({
        "date": [date(2024, 1, 1), date(2024, 1, 2), date(2024, 1, 3), date(2024, 1, 4), date(2024, 1, 5), date(2024, 1, 8), date(2024, 1, 9), date(2024, 1, 10)],
        "close": [100.0, 110.0, 105.0, 108.0, 112.0, 115.0, 114.0, 116.0],
        "open": [100.0, 110.0, 105.0, 108.0, 112.0, 115.0, 114.0, 116.0],
        "high": [100.0, 110.0, 105.0, 108.0, 112.0, 115.0, 114.0, 116.0],
        "low": [100.0, 110.0, 105.0, 108.0, 112.0, 115.0, 114.0, 116.0],
        "volume": [1000, 1100, 1200, 1300, 1400, 1500, 1600, 1700],
    })

    engineer = FeatureEngineer.__new__(FeatureEngineer)
    result = engineer._market_to_df([
        type("Row", (), {"date": r["date"], "open": r["open"], "high": r["high"], "low": r["low"], "close": r["close"], "adj_close": r["close"], "volume": r["volume"]})()
        for r in df.to_dict("records")
    ])
    result = validate_market_data(result, "LEAK")
    result["daily_return"] = engineer._calculate_returns(result["close"])
    result["volatility_5d"] = engineer._calculate_rolling_volatility(result["daily_return"], window=5)

    features_before = result["volatility_5d"].iloc[5]

    df_modified = df.copy()
    df_modified.loc[7, "close"] = 500.0
    result2 = engineer._market_to_df([
        type("Row", (), {"date": r["date"], "open": r["open"], "high": r["high"], "low": r["low"], "close": r["close"], "adj_close": r["close"], "volume": r["volume"]})()
        for r in df_modified.to_dict("records")
    ])
    result2 = validate_market_data(result2, "LEAK")
    result2["daily_return"] = engineer._calculate_returns(result2["close"])
    result2["volatility_5d"] = engineer._calculate_rolling_volatility(result2["daily_return"], window=5)

    features_after = result2["volatility_5d"].iloc[5]
    assert np.isfinite(features_before), "Original feature should be finite"
    assert np.isclose(features_before, features_after), "Future data change leaked into past features"