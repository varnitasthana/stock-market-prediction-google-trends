# Backend Tests

## Test database

Tests run against a dedicated PostgreSQL database:

`postgresql+asyncpg://postgres:postgres@localhost:5432/stock_prediction_test`

## Running tests

```bash
cd backend
python -m pytest tests/test_api_search_terms.py -v
```

## Test isolation

Each test gets a fresh schema via `drop_all` / `create_all`.
No test depends on state from a previous test.
