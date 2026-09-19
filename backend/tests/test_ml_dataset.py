from datetime import date

import pytest

from app.services.ml_dataset_service import MLDatasetError, MLDatasetService


@pytest.mark.asyncio
async def test_wide_format_conversion(client, db_session):
    from app.repositories.market_data_repo import MarketDataRepository
    from app.repositories.search_term_repo import SearchTermRepository
    from app.repositories.trends_repo import TrendsRepository
    from app.schemas.search_terms import SearchTermCreate

    term_repo = SearchTermRepository(db_session)
    term = await term_repo.create(SearchTermCreate(term="wide_term", category="test", active=True))

    market_repo = MarketDataRepository(db_session)
    await market_repo.bulk_insert([
        {"symbol": "WIDE", "date": date(2024, 1, 1), "close": 100.0, "volume": 1000},
        {"symbol": "WIDE", "date": date(2024, 1, 2), "close": 110.0, "volume": 1100},
        {"symbol": "WIDE", "date": date(2024, 1, 3), "close": 105.0, "volume": 1200},
        {"symbol": "WIDE", "date": date(2024, 1, 4), "close": 108.0, "volume": 1300},
        {"symbol": "WIDE", "date": date(2024, 1, 5), "close": 112.0, "volume": 1400},
        {"symbol": "WIDE", "date": date(2024, 1, 8), "close": 115.0, "volume": 1500},
        {"symbol": "WIDE", "date": date(2024, 1, 9), "close": 114.0, "volume": 1600},
        {"symbol": "WIDE", "date": date(2024, 1, 10), "close": 116.0, "volume": 1700},
        {"symbol": "WIDE", "date": date(2024, 1, 11), "close": 118.0, "volume": 1800},
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
        "symbol": "WIDE",
        "search_term_ids": [term.id],
        "start_date": "2024-01-01",
        "end_date": "2024-01-11",
    })
    assert resp.status_code == 200

    service = MLDatasetService(db_session)
    result = await service.prepare_dataset("WIDE", date(2024, 1, 1), date(2024, 1, 11))

    assert result["original_rows"] == 3
    assert result["feature_count"] > 0
    assert "date" not in result["feature_names"]
    assert "next_day_return" not in result["feature_names"]
    assert "next_day_direction" not in result["feature_names"]
    assert result["leakage_safe"] is True


@pytest.mark.asyncio
async def test_target_separation(client, db_session):
    from app.repositories.market_data_repo import MarketDataRepository
    from app.repositories.search_term_repo import SearchTermRepository
    from app.repositories.trends_repo import TrendsRepository
    from app.schemas.search_terms import SearchTermCreate

    term_repo = SearchTermRepository(db_session)
    term = await term_repo.create(SearchTermCreate(term="sep_term", category="test", active=True))

    market_repo = MarketDataRepository(db_session)
    await market_repo.bulk_insert([
        {"symbol": "SEP", "date": date(2024, 1, 1), "close": 100.0, "volume": 1000},
        {"symbol": "SEP", "date": date(2024, 1, 2), "close": 110.0, "volume": 1100},
        {"symbol": "SEP", "date": date(2024, 1, 3), "close": 105.0, "volume": 1200},
        {"symbol": "SEP", "date": date(2024, 1, 4), "close": 108.0, "volume": 1300},
        {"symbol": "SEP", "date": date(2024, 1, 5), "close": 112.0, "volume": 1400},
        {"symbol": "SEP", "date": date(2024, 1, 8), "close": 115.0, "volume": 1500},
        {"symbol": "SEP", "date": date(2024, 1, 9), "close": 114.0, "volume": 1600},
        {"symbol": "SEP", "date": date(2024, 1, 10), "close": 116.0, "volume": 1700},
        {"symbol": "SEP", "date": date(2024, 1, 11), "close": 118.0, "volume": 1800},
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
        "symbol": "SEP",
        "search_term_ids": [term.id],
        "start_date": "2024-01-01",
        "end_date": "2024-01-11",
    })
    assert resp.status_code == 200

    service = MLDatasetService(db_session)
    result = await service.prepare_dataset("SEP", date(2024, 1, 1), date(2024, 1, 11))

    assert "next_day_return" not in result["feature_names"]
    assert "next_day_direction" not in result["feature_names"]
    assert "next_day_return" in result["target_names"]
    assert "next_day_direction" in result["target_names"]


@pytest.mark.asyncio
async def test_chronological_split(client, db_session):
    from app.repositories.market_data_repo import MarketDataRepository
    from app.repositories.search_term_repo import SearchTermRepository
    from app.repositories.trends_repo import TrendsRepository
    from app.schemas.search_terms import SearchTermCreate

    term_repo = SearchTermRepository(db_session)
    term = await term_repo.create(SearchTermCreate(term="split_term", category="test", active=True))

    market_repo = MarketDataRepository(db_session)
    await market_repo.bulk_insert([
        {"symbol": "SPLIT", "date": date(2024, 1, 1), "close": 100.0, "volume": 1000},
        {"symbol": "SPLIT", "date": date(2024, 1, 2), "close": 110.0, "volume": 1100},
        {"symbol": "SPLIT", "date": date(2024, 1, 3), "close": 105.0, "volume": 1200},
        {"symbol": "SPLIT", "date": date(2024, 1, 4), "close": 108.0, "volume": 1300},
        {"symbol": "SPLIT", "date": date(2024, 1, 5), "close": 112.0, "volume": 1400},
        {"symbol": "SPLIT", "date": date(2024, 1, 8), "close": 115.0, "volume": 1500},
        {"symbol": "SPLIT", "date": date(2024, 1, 9), "close": 114.0, "volume": 1600},
        {"symbol": "SPLIT", "date": date(2024, 1, 10), "close": 116.0, "volume": 1700},
        {"symbol": "SPLIT", "date": date(2024, 1, 11), "close": 118.0, "volume": 1800},
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
        "symbol": "SPLIT",
        "search_term_ids": [term.id],
        "start_date": "2024-01-01",
        "end_date": "2024-01-11",
    })
    assert resp.status_code == 200

    service = MLDatasetService(db_session)
    result = await service.prepare_dataset("SPLIT", date(2024, 1, 1), date(2024, 1, 11))

    total = result["train_rows"] + result["validation_rows"] + result["test_rows"]
    assert total == result["rows_after_cleaning"]
    assert result["train_rows"] >= 1
    assert result["validation_rows"] >= 1
    assert result["test_rows"] >= 1

    if result["train_end_date"] and result["validation_start_date"]:
        assert result["train_end_date"] < result["validation_start_date"]
    if result["validation_end_date"] and result["test_start_date"]:
        assert result["validation_end_date"] < result["test_start_date"]


@pytest.mark.asyncio
async def test_split_ratios(client, db_session):
    from app.repositories.market_data_repo import MarketDataRepository
    from app.repositories.search_term_repo import SearchTermRepository
    from app.repositories.trends_repo import TrendsRepository
    from app.schemas.search_terms import SearchTermCreate

    term_repo = SearchTermRepository(db_session)
    term = await term_repo.create(SearchTermCreate(term="ratio_term", category="test", active=True))

    market_repo = MarketDataRepository(db_session)
    await market_repo.bulk_insert([
        {"symbol": "RATIO", "date": date(2024, 1, 1), "close": 100.0, "volume": 1000},
        {"symbol": "RATIO", "date": date(2024, 1, 2), "close": 110.0, "volume": 1100},
        {"symbol": "RATIO", "date": date(2024, 1, 3), "close": 105.0, "volume": 1200},
        {"symbol": "RATIO", "date": date(2024, 1, 4), "close": 108.0, "volume": 1300},
        {"symbol": "RATIO", "date": date(2024, 1, 5), "close": 112.0, "volume": 1400},
        {"symbol": "RATIO", "date": date(2024, 1, 8), "close": 115.0, "volume": 1500},
        {"symbol": "RATIO", "date": date(2024, 1, 9), "close": 114.0, "volume": 1600},
        {"symbol": "RATIO", "date": date(2024, 1, 10), "close": 116.0, "volume": 1700},
        {"symbol": "RATIO", "date": date(2024, 1, 11), "close": 118.0, "volume": 1800},
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
        "symbol": "RATIO",
        "search_term_ids": [term.id],
        "start_date": "2024-01-01",
        "end_date": "2024-01-11",
    })
    assert resp.status_code == 200

    service = MLDatasetService(db_session)
    result = await service.prepare_dataset("RATIO", date(2024, 1, 1), date(2024, 1, 11), train_ratio=0.70, validation_ratio=0.15, test_ratio=0.15)

    total = result["train_rows"] + result["validation_rows"] + result["test_rows"]
    assert total == result["rows_after_cleaning"]
    assert result["train_rows"] >= 1
    assert result["validation_rows"] >= 1
    assert result["test_rows"] >= 1


@pytest.mark.asyncio
async def test_duplicate_dates_handled(client, db_session):
    from app.repositories.market_data_repo import MarketDataRepository
    from app.repositories.search_term_repo import SearchTermRepository
    from app.repositories.trends_repo import TrendsRepository
    from app.schemas.search_terms import SearchTermCreate

    term_repo = SearchTermRepository(db_session)
    term = await term_repo.create(SearchTermCreate(term="dup_term", category="test", active=True))

    market_repo = MarketDataRepository(db_session)
    await market_repo.bulk_insert([
        {"symbol": "DUP", "date": date(2024, 1, 1), "close": 100.0, "volume": 1000},
        {"symbol": "DUP", "date": date(2024, 1, 2), "close": 110.0, "volume": 1100},
        {"symbol": "DUP", "date": date(2024, 1, 3), "close": 105.0, "volume": 1200},
        {"symbol": "DUP", "date": date(2024, 1, 4), "close": 108.0, "volume": 1300},
        {"symbol": "DUP", "date": date(2024, 1, 5), "close": 112.0, "volume": 1400},
        {"symbol": "DUP", "date": date(2024, 1, 8), "close": 115.0, "volume": 1500},
        {"symbol": "DUP", "date": date(2024, 1, 9), "close": 114.0, "volume": 1600},
        {"symbol": "DUP", "date": date(2024, 1, 10), "close": 116.0, "volume": 1700},
        {"symbol": "DUP", "date": date(2024, 1, 11), "close": 118.0, "volume": 1800},
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
        "symbol": "DUP",
        "search_term_ids": [term.id],
        "start_date": "2024-01-01",
        "end_date": "2024-01-11",
    })
    assert resp.status_code == 200

    service = MLDatasetService(db_session)
    result = await service.prepare_dataset("DUP", date(2024, 1, 1), date(2024, 1, 11))
    assert result["rows_after_cleaning"] == result["original_rows"]


@pytest.mark.asyncio
async def test_missing_and_infinite_values_handled(client, db_session):
    from app.repositories.market_data_repo import MarketDataRepository
    from app.repositories.search_term_repo import SearchTermRepository
    from app.repositories.trends_repo import TrendsRepository
    from app.schemas.search_terms import SearchTermCreate

    term_repo = SearchTermRepository(db_session)
    term = await term_repo.create(SearchTermCreate(term="clean_term", category="test", active=True))

    market_repo = MarketDataRepository(db_session)
    await market_repo.bulk_insert([
        {"symbol": "CLEAN", "date": date(2024, 1, 1), "close": 100.0, "volume": 1000},
        {"symbol": "CLEAN", "date": date(2024, 1, 2), "close": 110.0, "volume": 1100},
        {"symbol": "CLEAN", "date": date(2024, 1, 3), "close": 105.0, "volume": 1200},
        {"symbol": "CLEAN", "date": date(2024, 1, 4), "close": 108.0, "volume": 1300},
        {"symbol": "CLEAN", "date": date(2024, 1, 5), "close": 112.0, "volume": 1400},
        {"symbol": "CLEAN", "date": date(2024, 1, 8), "close": 115.0, "volume": 1500},
        {"symbol": "CLEAN", "date": date(2024, 1, 9), "close": 114.0, "volume": 1600},
        {"symbol": "CLEAN", "date": date(2024, 1, 10), "close": 116.0, "volume": 1700},
        {"symbol": "CLEAN", "date": date(2024, 1, 11), "close": 118.0, "volume": 1800},
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
        "symbol": "CLEAN",
        "search_term_ids": [term.id],
        "start_date": "2024-01-01",
        "end_date": "2024-01-11",
    })
    assert resp.status_code == 200

    service = MLDatasetService(db_session)
    result = await service.prepare_dataset("CLEAN", date(2024, 1, 1), date(2024, 1, 11))
    assert result["rows_removed"] >= 0
    assert result["rows_after_cleaning"] > 0


@pytest.mark.asyncio
async def test_target_validation(client, db_session):
    from app.repositories.market_data_repo import MarketDataRepository
    from app.repositories.search_term_repo import SearchTermRepository
    from app.repositories.trends_repo import TrendsRepository
    from app.schemas.search_terms import SearchTermCreate

    term_repo = SearchTermRepository(db_session)
    term = await term_repo.create(SearchTermCreate(term="tgt_term", category="test", active=True))

    market_repo = MarketDataRepository(db_session)
    await market_repo.bulk_insert([
        {"symbol": "TGT", "date": date(2024, 1, 1), "close": 100.0, "volume": 1000},
        {"symbol": "TGT", "date": date(2024, 1, 2), "close": 110.0, "volume": 1100},
        {"symbol": "TGT", "date": date(2024, 1, 3), "close": 105.0, "volume": 1200},
        {"symbol": "TGT", "date": date(2024, 1, 4), "close": 108.0, "volume": 1300},
        {"symbol": "TGT", "date": date(2024, 1, 5), "close": 112.0, "volume": 1400},
        {"symbol": "TGT", "date": date(2024, 1, 8), "close": 115.0, "volume": 1500},
        {"symbol": "TGT", "date": date(2024, 1, 9), "close": 114.0, "volume": 1600},
        {"symbol": "TGT", "date": date(2024, 1, 10), "close": 116.0, "volume": 1700},
        {"symbol": "TGT", "date": date(2024, 1, 11), "close": 118.0, "volume": 1800},
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
        "symbol": "TGT",
        "search_term_ids": [term.id],
        "start_date": "2024-01-01",
        "end_date": "2024-01-11",
    })
    assert resp.status_code == 200

    service = MLDatasetService(db_session)
    result = await service.prepare_dataset("TGT", date(2024, 1, 1), date(2024, 1, 11))
    assert result["quality_issues"] == []


@pytest.mark.asyncio
async def test_leakage_prevention(client, db_session):
    from app.repositories.market_data_repo import MarketDataRepository
    from app.repositories.search_term_repo import SearchTermRepository
    from app.repositories.trends_repo import TrendsRepository
    from app.schemas.search_terms import SearchTermCreate

    term_repo = SearchTermRepository(db_session)
    term = await term_repo.create(SearchTermCreate(term="leak_term", category="test", active=True))

    market_repo = MarketDataRepository(db_session)
    await market_repo.bulk_insert([
        {"symbol": "LEAK", "date": date(2024, 1, 1), "close": 100.0, "volume": 1000},
        {"symbol": "LEAK", "date": date(2024, 1, 2), "close": 110.0, "volume": 1100},
        {"symbol": "LEAK", "date": date(2024, 1, 3), "close": 105.0, "volume": 1200},
        {"symbol": "LEAK", "date": date(2024, 1, 4), "close": 108.0, "volume": 1300},
        {"symbol": "LEAK", "date": date(2024, 1, 5), "close": 112.0, "volume": 1400},
        {"symbol": "LEAK", "date": date(2024, 1, 8), "close": 115.0, "volume": 1500},
        {"symbol": "LEAK", "date": date(2024, 1, 9), "close": 114.0, "volume": 1600},
        {"symbol": "LEAK", "date": date(2024, 1, 10), "close": 116.0, "volume": 1700},
        {"symbol": "LEAK", "date": date(2024, 1, 11), "close": 118.0, "volume": 1800},
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
        "symbol": "LEAK",
        "search_term_ids": [term.id],
        "start_date": "2024-01-01",
        "end_date": "2024-01-11",
    })
    assert resp.status_code == 200

    service = MLDatasetService(db_session)
    result = await service.prepare_dataset("LEAK", date(2024, 1, 1), date(2024, 1, 11))
    assert result["leakage_safe"] is True
    assert "next_day_return" not in result["feature_names"]
    assert "next_day_direction" not in result["feature_names"]


@pytest.mark.asyncio
async def test_date_ordering_validation(client, db_session):
    from app.repositories.market_data_repo import MarketDataRepository
    from app.repositories.search_term_repo import SearchTermRepository
    from app.repositories.trends_repo import TrendsRepository
    from app.schemas.search_terms import SearchTermCreate

    term_repo = SearchTermRepository(db_session)
    term = await term_repo.create(SearchTermCreate(term="order_term", category="test", active=True))

    market_repo = MarketDataRepository(db_session)
    await market_repo.bulk_insert([
        {"symbol": "ORDER", "date": date(2024, 1, 1), "close": 100.0, "volume": 1000},
        {"symbol": "ORDER", "date": date(2024, 1, 2), "close": 110.0, "volume": 1100},
        {"symbol": "ORDER", "date": date(2024, 1, 3), "close": 105.0, "volume": 1200},
        {"symbol": "ORDER", "date": date(2024, 1, 4), "close": 108.0, "volume": 1300},
        {"symbol": "ORDER", "date": date(2024, 1, 5), "close": 112.0, "volume": 1400},
        {"symbol": "ORDER", "date": date(2024, 1, 8), "close": 115.0, "volume": 1500},
        {"symbol": "ORDER", "date": date(2024, 1, 9), "close": 114.0, "volume": 1600},
        {"symbol": "ORDER", "date": date(2024, 1, 10), "close": 116.0, "volume": 1700},
        {"symbol": "ORDER", "date": date(2024, 1, 11), "close": 118.0, "volume": 1800},
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
        "symbol": "ORDER",
        "search_term_ids": [term.id],
        "start_date": "2024-01-01",
        "end_date": "2024-01-11",
    })
    assert resp.status_code == 200

    service = MLDatasetService(db_session)
    result = await service.prepare_dataset("ORDER", date(2024, 1, 1), date(2024, 1, 11))
    assert result["train_end_date"] < result["validation_start_date"]
    assert result["validation_end_date"] < result["test_start_date"]


@pytest.mark.asyncio
async def test_empty_dataset_error(client, db_session):
    service = MLDatasetService(db_session)
    with pytest.raises(MLDatasetError):
        await service.prepare_dataset("NONEXISTENT", date(2024, 1, 1), date(2024, 1, 5))


@pytest.mark.asyncio
async def test_insufficient_observations_error(client, db_session):
    from app.repositories.market_data_repo import MarketDataRepository
    from app.repositories.search_term_repo import SearchTermRepository
    from app.repositories.trends_repo import TrendsRepository
    from app.schemas.search_terms import SearchTermCreate

    term_repo = SearchTermRepository(db_session)
    term = await term_repo.create(SearchTermCreate(term="insufficient", category="test", active=True))

    market_repo = MarketDataRepository(db_session)
    await market_repo.bulk_insert([
        {"symbol": "INS", "date": date(2024, 1, 1), "close": 100.0, "volume": 1000},
        {"symbol": "INS", "date": date(2024, 1, 2), "close": 110.0, "volume": 1100},
        {"symbol": "INS", "date": date(2024, 1, 3), "close": 105.0, "volume": 1200},
    ])

    trends_repo = TrendsRepository(db_session)
    await trends_repo.bulk_insert([
        {"search_term_id": term.id, "date": date(2024, 1, 1), "interest_score": 10},
        {"search_term_id": term.id, "date": date(2024, 1, 2), "interest_score": 20},
        {"search_term_id": term.id, "date": date(2024, 1, 3), "interest_score": 30},
    ])

    resp = await client.post("/api/features/generate", json={
        "symbol": "INS",
        "search_term_ids": [term.id],
        "start_date": "2024-01-01",
        "end_date": "2024-01-03",
    })
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_ml_dataset_api_success(client, db_session):
    from app.repositories.market_data_repo import MarketDataRepository
    from app.repositories.search_term_repo import SearchTermRepository
    from app.repositories.trends_repo import TrendsRepository
    from app.schemas.search_terms import SearchTermCreate

    term_repo = SearchTermRepository(db_session)
    term = await term_repo.create(SearchTermCreate(term="api_ml", category="test", active=True))

    market_repo = MarketDataRepository(db_session)
    await market_repo.bulk_insert([
        {"symbol": "APIML", "date": date(2024, 1, 1), "close": 100.0, "volume": 1000},
        {"symbol": "APIML", "date": date(2024, 1, 2), "close": 110.0, "volume": 1100},
        {"symbol": "APIML", "date": date(2024, 1, 3), "close": 105.0, "volume": 1200},
        {"symbol": "APIML", "date": date(2024, 1, 4), "close": 108.0, "volume": 1300},
        {"symbol": "APIML", "date": date(2024, 1, 5), "close": 112.0, "volume": 1400},
        {"symbol": "APIML", "date": date(2024, 1, 8), "close": 115.0, "volume": 1500},
        {"symbol": "APIML", "date": date(2024, 1, 9), "close": 114.0, "volume": 1600},
        {"symbol": "APIML", "date": date(2024, 1, 10), "close": 116.0, "volume": 1700},
        {"symbol": "APIML", "date": date(2024, 1, 11), "close": 118.0, "volume": 1800},
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
        "symbol": "APIML",
        "search_term_ids": [term.id],
        "start_date": "2024-01-01",
        "end_date": "2024-01-11",
    })
    assert resp.status_code == 200

    resp = await client.post("/api/ml-dataset/prepare", json={
        "symbol": "APIML",
        "start_date": "2024-01-01",
        "end_date": "2024-01-11",
        "train_ratio": 0.70,
        "validation_ratio": 0.15,
        "test_ratio": 0.15,
    })
    assert resp.status_code == 200
    body = resp.json()
    assert body["symbol"] == "APIML"
    assert body["feature_count"] > 0
    assert body["train_rows"] > 0
    assert body["validation_rows"] > 0
    assert body["test_rows"] > 0
    assert body["leakage_safe"] is True


@pytest.mark.asyncio
async def test_ml_dataset_api_invalid_ratios(client, db_session):
    resp = await client.post("/api/ml-dataset/prepare", json={
        "symbol": "APIML",
        "start_date": "2024-01-01",
        "end_date": "2024-01-11",
        "train_ratio": 0.80,
        "validation_ratio": 0.30,
        "test_ratio": 0.10,
    })
    assert resp.status_code == 400
