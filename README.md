# Stock Market Behaviour Prediction System Using Google Trends

> **Research project for educational and portfolio purposes only. This is NOT investment advice.**

A production-style end-to-end machine learning system that investigates whether changes in Google search interest for finance-related keywords are associated with subsequent stock-market behaviour for **NIFTY 50** and **SENSEX**.

The system estimates the probability/direction of subsequent market movement based on historical relationships between search activity and market features.

---

## Table of Contents

1. [Project Objective](#project-objective)
2. [Architecture](#architecture)
3. [Technology Stack](#technology-stack)
4. [Project Structure](#project-structure)
5. [Setup](#setup)
6. [Running the Application](#running-the-application)
7. [Running Tests](#running-tests)
8. [Docker](#docker)
9. [API Documentation](#api-documentation)
10. [ML Methodology](#ml-methodology)
11. [Limitations](#limitations)
12. [Future Improvements](#future-improvements)

---

## Project Objective

Build an end-to-end data analytics and machine learning pipeline that:
1. Collects Google Trends data for financial search terms.
2. Collects historical OHLCV market data for NIFTY 50 and SENSEX.
3. Cleans, normalizes, and aligns both datasets by trading date.
4. Engineers market features (returns, volatility, momentum) and search-trend features (changes, lags, rolling statistics).
5. Performs statistical analysis (Pearson, Spearman, lagged correlations).
6. Identifies statistically useful features.
7. Trains ML models (Logistic Regression, Random Forest, Gradient Boosting, XGBoost).
8. Evaluates models using proper time-series methodology (chronological splits, walk-forward validation).
9. Exposes predictions via REST APIs.
10. Provides a React dashboard for visualization.

---

## Architecture

```
Google Trends ──► Data Collection Layer ──► Search Data ─┐
                                                      │
yfinance   ──► Data Collection Layer ──► Market Data ──┤
                                                      ▼
                                              Data Cleaning
                                                      ▼
                                              Data Storage (PostgreSQL)
                                                      ▼
                                              Feature Engineering
                                                      ▼
                                              Statistical Analysis
                                                      ▼
                                              Feature Selection
                                                      ▼
                                              Machine Learning
                                                      ▼
                                              Model Evaluation
                                                      ▼
                                              Prediction API (FastAPI)
                                                      ▼
                                              React Dashboard
```

### Component Responsibilities

| Layer | Component | Responsibility |
|-------|-----------|----------------|
| API | `api/routers/*.py` | HTTP routing, validation, serialization |
| Schemas | `schemas/*.py` | Pydantic request/response DTOs |
| Services | `services/*.py` | Business logic and orchestration |
| Repositories | `repositories/*.py` | Database CRUD via SQLAlchemy |
| ML | `ml/*.py` | Feature engineering, model training, evaluation, prediction |
| Pipeline | `pipeline/*.py` | ETL orchestration |
| Utils | `utils/*.py` | Date helpers, validators, I/O |

---

## Technology Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| Backend | **Python 3.12+**, **FastAPI**, **Pydantic v2** | REST API, validation, async support |
| ORM | **SQLAlchemy 2.0** | Database access with asyncpg |
| Database | **PostgreSQL 16** | Persistent data storage |
| ML | **Pandas**, **NumPy**, **scikit-learn**, **XGBoost**, **scipy** | Data processing and modeling |
| Data Sources | **yfinance**, **pytrends** | Market and Google Trends data |
| Frontend | **React 18**, **TypeScript**, **Vite**, **Tailwind CSS**, **Recharts** | Dashboard |
| DevOps | **Docker**, **Docker Compose**, **pytest**, **Ruff** | Containerization, testing, linting |

---

## Project Structure

```
stock-market-behaviour-prediction/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                    # FastAPI entrypoint
│   │   ├── api/
│   │   │   ├── deps.py                # Shared dependencies
│   │   │   └── routers/               # API endpoints
│   │   │       ├── search_terms.py
│   │   │       ├── market_data.py
│   │   │       ├── trends.py
│   │   │       ├── features.py
│   │   │       ├── models.py
│   │   │       ├── predictions.py
│   │   │       └── dashboard.py
│   │   ├── core/
│   │   │   ├── config.py              # Pydantic settings
│   │   │   ├── database.py            # SQLAlchemy engine/session
│   │   │   └── logging.py             # Logging setup
│   │   ├── models/
│   │   │   └── database.py            # ORM models
│   │   ├── schemas/                   # Pydantic DTOs
│   │   ├── services/                  # Business logic
│   │   ├── repositories/              # Database access
│   │   ├── ml/                        # ML pipeline
│   │   │   ├── feature_engineer.py
│   │   │   ├── statistical_analyzer.py
│   │   │   ├── model_trainer.py
│   │   │   ├── evaluator.py
│   │   │   └── predictor.py
│   │   ├── pipeline/                  # ETL pipelines
│   │   │   ├── market_pipeline.py
│   │   │   ├── trends_pipeline.py
│   │   │   ├── feature_pipeline.py
│   │   │   └── run.py
│   │   └── utils/                     # Helpers
│   ├── tests/
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── services/
│   │   ├── hooks/
│   │   ├── types/
│   │   └── App.tsx
│   ├── package.json
│   └── Dockerfile
├── data/
│   ├── raw/
│   ├── processed/
│   └── README.md
├── notebooks/
│   ├── exploratory_analysis.ipynb
│   └── model_experiments.ipynb
├── docker-compose.yml
├── .env.example
├── .gitignore
├── README.md
└── LICENSE
```

---

## Live Development Access

### Local Development

| Service | URL |
|---------|-----|
| Frontend | http://localhost:5173 |
| Backend API | http://localhost:8000 |
| Swagger UI | http://localhost:8000/docs |
| OpenAPI JSON | http://localhost:8000/openapi.json |
| Health Check | http://localhost:8000/api/health |

### Public Deployment

**Public URL:** NOT DEPLOYED YET

This project runs locally only. No public hosting is configured.

---

## How to Start the Project

### Option 1: Docker Compose (Recommended)

```bash
docker compose up --build
```

Services:
- Backend: http://localhost:8000
- Frontend: http://localhost:5173
- PostgreSQL: localhost:5432

### Option 2: Manual

**Terminal 1 — PostgreSQL:**
```bash
docker compose up -d postgres
```

**Terminal 2 — Backend:**
```bash
cd backend
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

**Terminal 3 — Frontend:**
```bash
cd frontend
npm install
npm run dev
```

---

## Running Tests

```bash
cd backend
pytest -v
```

Tests run against a dedicated PostgreSQL test database:
`postgresql+asyncpg://postgres:postgres@localhost:5432/stock_prediction_test`

Each test creates a fresh schema via `drop_all` / `create_all` and disposes the engine afterward.

---

## Google Trends Pipeline

### Overview

Phase 4 implements a Google Trends ingestion pipeline that:

1. Retrieves active search terms from the database.
2. Fetches interest-over-time data from Google Trends via `pytrends`.
3. Normalizes the external response into the project's internal schema.
4. Persists records to PostgreSQL while preventing duplicates.

### Architecture

```
HTTP Request
    ↓
FastAPI Router (`POST /api/trends/ingest`)
    ↓
Pydantic Schema (`TrendsIngestRequest`)
    ↓
Trends Ingestion Service
    ↓
Trends Data Provider (abstraction)
    ↓
Pytrends Provider (implementation)
    ↓
Google Trends
```

Persistence:

```
Trends Ingestion Service
    ↓
Trends Repository
    ↓
SQLAlchemy AsyncSession
    ↓
PostgreSQL
```

### Provider Abstraction

The project uses a `TrendsDataProvider` interface so the external Google Trends client can be changed without rewriting the ingestion service.

Current implementation: `PytrendsProvider` wrapping `pytrends`.

### Error Handling

- `404` — search term not found
- `502` — external Google Trends provider unavailable or returned invalid data
- `422` — invalid request payload

### Rate Limiting

The provider includes a configurable delay (`PYTRENDS_SLEEP`) between requests to reduce the risk of rate limiting by Google Trends.

### Retries

The provider uses bounded retries through `pytrends`'s built-in retry configuration.

---

## Setup

### Prerequisites

- Python 3.12+
- Node.js 20+
- PostgreSQL 16 (or use Docker)

### Backend Setup

```bash
cd backend
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
```

### Frontend Setup

```bash
cd frontend
npm install
```

### Environment Variables

Copy `.env.example` to `.env` and configure:

```env
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/stock_prediction
API_ENV=development
LOG_LEVEL=INFO
PYTRENDS_RETRIES=3
PYTRENDS_SLEEP=1
DEFAULT_MARKET_SYMBOL=NSEI
DEFAULT_START_DATE=2018-01-01
DEFAULT_END_DATE=2025-01-01
```

---

## Running the Application

### Option 1: Docker Compose (Recommended)

```bash
docker compose up --build
```

Services:
- Backend: http://localhost:8000
- Frontend: http://localhost:5173
- PostgreSQL: localhost:5432

### Option 2: Manual

**Backend:**
```bash
cd backend
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

**Frontend:**
```bash
cd frontend
npm run dev
```

**Database:**
```bash
# Create database manually or via docker
psql -U postgres -c "CREATE DATABASE stock_prediction;"
```

---

## Running Tests

```bash
cd backend
pytest -v
```

---

## API Documentation

FastAPI auto-generates interactive API documentation:

- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

### Key Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/health` | Health check |
| GET | `/api/search-terms/` | List search terms |
| POST | `/api/search-terms/` | Add search term |
| GET | `/api/search-terms/{id}` | Get search term |
| PUT | `/api/search-terms/{id}` | Update search term |
| DELETE | `/api/search-terms/{id}` | Delete search term |
| GET | `/api/trends/` | Get trends data for a term |
| GET | `/api/trends/recent/{search_term_id}` | Get recent trends |
| POST | `/api/trends/ingest` | Ingest Google Trends data |
| POST | `/api/alignment/` | Align market and trends data |
| GET | `/api/market-data/` | Get market data |
| GET | `/api/market-data/recent/{symbol}` | Get recent market data |
| POST | `/api/market-data/ingest` | Ingest market data from yfinance |
| GET | `/api/features/` | Get engineered features |
| POST | `/api/features/generate` | Generate and persist engineered features |
| GET | `/api/models/` | List model runs |
| POST | `/api/models/` | Create model run |
| GET | `/api/predictions/` | Get predictions |
| GET | `/api/dashboard/summary` | Dashboard summary |

### Trends Ingestion

Ingest Google Trends data for a configured search term:

```http
POST /api/trends/ingest
Content-Type: application/json

{
  "search_term_id": 1,
  "start_date": "2024-01-01",
  "end_date": "2024-01-07"
}
```

Response:

```json
{
  "requested_term_ids": [1],
  "results": [
    {
      "term": "recession",
      "total_records": 5,
      "inserted": 5,
      "duplicates_skipped": 0,
      "error": null
    }
  ],
  "total_inserted": 5,
  "total_duplicates_skipped": 0
}
```

Notes:
- Only active search terms should be used for ingestion.
- Duplicate dates for the same search term are automatically skipped.
- The endpoint returns `502 Bad Gateway` if the external Google Trends provider is unavailable.

---

## Data Cleaning & Temporal Alignment

### Overview

Phase 5 implements data cleaning and temporal alignment for Google Trends and market data.

The goal is to make raw data from both sources reliable and temporally compatible for feature engineering and ML.

### Cleaning Rules

#### Google Trends

- Interest score must be numeric.
- Interest score is preserved on its native 0–100 scale. Zero is a valid value and is not converted to NULL.
- Records with missing dates or missing interest scores are dropped.
- Duplicate `(search_term_id, date)` rows are deduplicated.
- Provider metadata such as `isPartial` is removed.
- Dates are sorted in ascending order.

#### Market Data

- Required fields: `date`, `close`, `volume`.
- `close` must be positive; non-positive values are logged as warnings.
- `volume` must be non-negative; negative values are logged as warnings.
- For OHLC data, logical consistency is checked:
  - `high >= open`, `high >= close`, `high >= low`
  - `low <= open`, `low <= close`
- Duplicate `(symbol, date)` rows are deduplicated.
- Dates are sorted in ascending order.

### Temporal Alignment

Market trading dates are used as the primary timeline.

Google Trends observations are aligned to market dates using explicit date matching.

```
Market dates: 2024-01-01, 2024-01-02, 2024-01-03, 2024-01-04, 2024-01-05
Trends dates: 2024-01-01, 2024-01-02, 2024-01-04

Aligned result:
  date        | close | interest_score
  2024-01-01  | 100   | 10
  2024-01-02  | 101   | 20
  2024-01-04  | 103   | 40
```

Unmatched dates are reported but not invented.

Weekends and market holidays are not treated as missing market observations.

### Data Quality Report

The alignment API returns a quality report:

```json
{
  "market_rows": 5,
  "trends_rows": 3,
  "valid_market_rows": 5,
  "valid_trends_rows": 3,
  "duplicate_market_rows": 0,
  "duplicate_trends_rows": 0,
  "aligned_rows": 3,
  "unmatched_market_dates": ["2024-01-03"],
  "unmatched_trends_dates": []
}
```

### Leakage Prevention

- Aligned rows never use future market or trends observations.
- Date-based joins prevent row-number matching errors.
- The alignment is deterministic and reproducible.

### Alignment API

```http
POST /api/alignment/
Content-Type: application/json

{
  "symbol": "NSEI",
  "search_term_id": 1,
  "start_date": "2024-01-01",
  "end_date": "2024-01-07"
}
```

Response includes aligned rows and a data quality report.

---

## Feature Engineering

### Overview

Phase 6 transforms cleaned and temporally aligned market + Google Trends data into meaningful features for machine learning.

The feature-engineering process is deterministic and uses only information available at or before each prediction date.

### Pipeline

```
API / Pipeline
      ↓
Fetch cleaned/aligned data
      ↓
Feature Engineering Service
      ↓
Calculate market features
      ↓
Calculate Trends features
      ↓
Generate targets
      ↓
Remove insufficient rows
      ↓
Validate ML-ready dataset
      ↓
Persist engineered features
```

### Feature Storage

Features are stored in the `engineered_features` table with a unique constraint on `(symbol, date, feature_name)`. This allows:
- Idempotent feature generation (re-running does not create duplicates)
- Efficient querying by symbol and date range
- Dynamic feature names per search term

### Market Features

| Feature | Formula | Description |
|---------|---------|-------------|
| `daily_return` | `(close_t / close_{t-1}) - 1` | Percentage change from previous trading day |
| `log_return` | `ln(close_t / close_{t-1})` | Log returns for statistical modeling |
| `volatility_5d` | 5-day rolling std of returns | Historical volatility measure |
| `return_lag_1` | `daily_return_{t-1}` | Previous day's return |
| `return_lag_3` | `daily_return_{t-3}` | 3-day lagged return |
| `return_lag_5` | `daily_return_{t-5}` | 5-day lagged return |

### Google Trends Features

For each active search term stored in the database, dynamic features are generated using a sanitized term name.

Example: search term `"interest rates"` becomes prefix `interest_rates`.

| Feature | Description |
|---------|-------------|
| `{term}_trend` | Current interest score aligned to market date |
| `{term}_trend_lag_1` | Previous day's interest score |
| `{term}_trend_lag_3` | 3-day lagged interest score |
| `{term}_trend_lag_7` | 7-day lagged interest score |
| `{term}_trend_change` | Day-over-day change in interest score |

### Target Variables

Targets use future information by definition and are treated as **labels**, never as input features.

| Target | Formula | Description |
|--------|---------|-------------|
| `next_day_return` | `daily_return_{t+1}` | Return for the next trading day |
| `next_day_direction` | `1 if next_day_return > 0 else 0` | Binary direction of next-day movement |

### Feature vs Target Separation

```
Features available at date t:
  - today's Trends score
  - past returns (lag 1, 3, 5)
  - past volatility
  - past Trends lags and changes

Target generated from date t+1:
  - next_day_return
  - next_day_direction
```

### Leakage Prevention

- All rolling statistics use backward-looking windows only.
- Lag features use `.shift(1)`, `.shift(3)`, `.shift(5)`, `.shift(7)` — never centered windows.
- Targets use `.shift(-1)` and are only used as labels.
- Date-based alignment prevents row-position matching errors.
- A dedicated leakage test verifies that modifying future values does not change features for earlier dates.

### Missing Values

Initial rows with insufficient history are removed from the final ML-ready dataset:
- `daily_return` is NaN for the first row
- `volatility_5d` requires 5 prior return observations
- `return_lag_5` requires 5 prior returns
- `{term}_trend_lag_7` requires 7 prior trend observations

Rows with any NaN in required columns (`daily_return`, `volatility_5d`, `next_day_return`) are dropped. This strategy is appropriate because:
- Models cannot train on incomplete feature vectors
- The removed rows represent the warm-up period of the time series
- The strategy is deterministic and documented

### Multiple Search Terms

Search terms are dynamically read from the `search_terms` table. Each active term becomes a set of features with a sanitized name:

| Search Term | Feature Prefix |
|-------------|---------------|
| `recession` | `recession` |
| `inflation` | `inflation` |
| `interest rates` | `interest_rates` |
| `stock market` | `stock_market` |
| `unemployment` | `unemployment` |

No hardcoded term list is required.

### Validation

The generated feature dataset is validated for:
- Required columns exist
- Numeric features contain no NaN or infinite values
- No unexpected duplicate `(symbol, date)` records
- Target values are finite
- Features use only past/current information

### API

```http
POST /api/features/generate
Content-Type: application/json

{
  "symbol": "^NSEI",
  "search_term_ids": [3, 6, 7, 8, 9],
  "start_date": "2024-01-01",
  "end_date": "2024-06-30"
}
```

Response:
```json
{
  "symbol": "^NSEI",
  "rows_generated": 114,
  "rows_persisted": 3751,
  "features_generated": [
    "daily_return",
    "inflation_trend",
    "next_day_return",
    "next_day_direction",
    "volatility_5d",
    ...
  ]
}
```

### Idempotency

Re-running feature generation for the same symbol, date range, and search terms does not create duplicate rows. The `ON CONFLICT DO NOTHING` clause on `(symbol, date, feature_name)` ensures safe re-execution.

---

## Statistical Analysis

### Overview

Phase 7 investigates whether Google Trends variables have measurable statistical relationships with NIFTY 50 market behavior, using the Phase 6 engineered dataset.

This phase produces evidence for research questions such as:
- Are Google Trends scores correlated with market returns?
- Do lagged Google Trends variables relate to future returns?
- Are relationships different across search terms?
- Are observed associations statistically significant?

### Pipeline

```
Engineered Features
        ↓
Statistical Analysis Service
        ↓
Descriptive Statistics
        ↓
Correlation Analysis (Pearson + Spearman)
        ↓
Lag Analysis
        ↓
Direction Analysis
        ↓
Multiple-Testing Correction (Benjamini-Hochberg)
        ↓
Analysis Results
```

### Methods

| Method | Purpose |
|--------|---------|
| Descriptive statistics | Count, mean, median, std, min, max for relevant variables |
| Pearson correlation | Linear association between continuous variables |
| Spearman correlation | Monotonic association based on ranks |
| p-values | Statistical significance under the tested assumptions |
| Benjamini-Hochberg FDR | Multiple-testing correction for many feature-target pairs |
| Direction-group analysis | Compare Trends statistics for up vs down next-day movement |

### Correlation Targets

- `daily_return` — same-day market return
- `next_day_return` — next trading day's return

### Trends Features Analyzed

For each search term, the following features are analyzed dynamically:

- `{term}_trend`
- `{term}_trend_lag_1`
- `{term}_trend_lag_3`
- `{term}_trend_lag_7`
- `{term}_trend_change`

### Lag Analysis

Lagged Google Trends features are correlated with `next_day_return` to investigate whether prior search activity is associated with subsequent market behavior.

### Direction Analysis

Descriptive statistics are computed separately for:

- `next_day_direction = 0` (down or flat next day)
- `next_day_direction = 1` (up next day)

This compares average Trends scores between upward and downward movement dates.

### Multiple Testing

Because many search terms and lagged features are tested, the Benjamini-Hochberg false discovery rate (FDR) correction is applied to Pearson correlation p-values. This adjusts for the increased probability of false positives when performing multiple tests.

### API

```http
POST /api/statistics/analyze
Content-Type: application/json

{
  "symbol": "^NSEI",
  "start_date": "2024-01-01",
  "end_date": "2024-06-30"
}
```

Response includes descriptive statistics, correlations, lag analysis, and direction analysis.

### Interpretation

This phase measures **association, not causation**.

A statistically significant correlation indicates a detectable linear or monotonic relationship in the tested sample. It does **not** prove that Google Trends causes market movements, nor does it guarantee future predictive performance.

---

## ML Dataset Preparation

### Overview

Phase 8 transforms the Phase 6 engineered features into a clean, model-ready dataset for machine learning in Phase 9.

The dataset is prepared without training any models. The focus is on:
- Wide-format conversion
- Feature/target separation
- Chronological train/validation/test splitting
- Leakage prevention
- Data quality validation

### Pipeline

```
Engineered Features (long format)
        ↓
ML Dataset Service
        ↓
Pivot to wide format
        ↓
Identify features and targets
        ↓
Validate data quality
        ↓
Check for leakage
        ↓
Chronological train/validation/test split
        ↓
ML-ready datasets
```

### Wide-Format Conversion

The `engineered_features` table stores data in long format (one row per feature per date). Phase 8 pivots this into a wide-format DataFrame where:
- Each row is one trading date
- Each column is one feature or target
- Targets are explicitly separated from features

### Feature/Target Separation

**Features (X):**
- Market features: `daily_return`, `log_return`, `volatility_5d`, `return_lag_1`, `return_lag_3`, `return_lag_5`
- Trends features: `{term}_trend`, `{term}_trend_lag_1`, `{term}_trend_lag_3`, `{term}_trend_lag_7`, `{term}_trend_change`

**Targets (y):**
- `next_day_return` — regression target
- `next_day_direction` — classification target (0 or 1)

Targets are never included in the feature matrix.

### Chronological Splitting

Financial time-series must not be randomly shuffled. Phase 8 uses a chronological split:

```
Training   → earliest observations (default 70%)
Validation → middle observations (default 15%)
Test       → latest observations (default 15%)
```

This ensures that:
- Models are trained on historical data
- Validation is used for model-development decisions
- Test data remains completely unseen until final evaluation

Split ratios are configurable but must sum to 1.0.

### Leakage Prevention

Before splitting, Phase 8 explicitly verifies that:
- Target columns (`next_day_return`, `next_day_direction`) are not present in the feature matrix
- No future-looking feature names are included
- Train, validation, and test sets do not overlap chronologically

### Missing Values

Rows with missing target values (`next_day_return` or `next_day_direction`) are removed before splitting. This handles the warm-up period where insufficient history exists for lagged features. Missing values are not silently replaced with zero.

### Data Quality Checks

Before returning the ML dataset, Phase 8 validates:
- No duplicate dates
- No infinite values in numeric columns
- Classification target contains only 0 or 1
- Regression target is numeric and finite
- All required feature columns are present
- Chronological ordering is preserved

### API

```http
POST /api/ml-dataset/prepare
Content-Type: application/json

{
  "symbol": "^NSEI",
  "start_date": "2024-01-01",
  "end_date": "2024-06-30",
  "train_ratio": 0.70,
  "validation_ratio": 0.15,
  "test_ratio": 0.15
}
```

Response includes metadata about the prepared dataset, including row counts, feature names, date ranges, and leakage validation.

### Current Dataset

For the current real dataset (`^NSEI`, 2024-01-01 to 2024-06-30):
- Original rows: 114
- Features: 31
- Train: 79 rows (2024-01-08 to 2024-05-07)
- Validation: 17 rows (2024-05-08 to 2024-05-31)
- Test: 18 rows (2024-06-03 to 2024-06-27)

### Limitations

- The current dataset contains only 114 observations (approximately six months).
- This is a relatively small sample for financial machine learning.
- Phase 8 does not scale or select features; that is left to Phase 9.
- The split ratios are a design choice for this college project, not a claim of universal optimality.

---

## ML Methodology

### Feature Engineering

**Market Features:**
- Daily return: `(close_t / close_{t-1}) - 1`
- Rolling returns: 5-day, 10-day, 20-day
- Moving averages: 5, 10, 20-day
- Momentum: 5-day, 10-day
- Volatility: 5, 10, 20-day rolling standard deviation
- Volume change: percentage change in volume

**Search Trends Features:**
- Current interest score
- Lagged interest: lag 1, 3, 5, 7
- Interest change: 1-day, 3-day, 7-day
- Percentage change
- Rolling averages: 3-day, 7-day
- Rolling standard deviations: 3-day, 7-day
- Interest momentum

### Target Variable

**Classification (direction):**
```
target_direction = 1 if next_day_return > 0 else 0
```

**Regression (return):**
```
target_return = next_day_return
```

### Time-Series Validation

- **Chronological split:** Train on historical data, validate/test on future data
- **Walk-forward validation:** Expanding window training to simulate real-world deployment
- **No random shuffling:** Preserves temporal order
- **No data leakage:** Features are constructed using only information available at time t

### Models

1. **Baseline:** Majority class
2. **Logistic Regression:** Interpretable linear baseline
3. **Random Forest:** Non-linear relationships
4. **Gradient Boosting:** Advanced ensemble
5. **XGBoost:** State-of-the-art gradient boosting

---

## Limitations

- Correlation does not imply causation.
- Google Trends provides **relative** search interest, not absolute search volume.
- Financial time-series are noisy, non-stationary, and influenced by countless external factors.
- This system is for **research and educational purposes only**.
- Past performance does not guarantee future results.
- This is NOT investment advice.

---

## Phase 9 — Model Training

Phase 9 builds on the leakage-safe ML dataset prepared in Phase 8 and trains baseline machine-learning models.

### What it does

It takes the chronological train/validation/test splits from Phase 8 and fits four baseline models:

**Classification**

Predicts `next_day_direction` using:

- Logistic Regression
- Random Forest Classifier

**Regression**

Predicts `next_day_return` using:

- Linear Regression
- Random Forest Regressor

### Why model-specific preprocessing

Logistic Regression and Linear Regression benefit from standardized features, so they are wrapped in a `StandardScaler` pipeline fitted **only on the training data**.

Random Forest models are tree-based and do not require feature scaling.

### Why the test set remains untouched

The test set is reserved for final evaluation in Phase 10. Phase 9 only verifies that training completes successfully.

### Current limitation

The dataset has only 114 observations. Results must be interpreted cautiously.

### Training API

```http
POST /api/models/train
```

Example request:

```json
{
  "symbol": "^NSEI",
  "start_date": "2024-01-01",
  "end_date": "2024-06-30",
  "task": "classification",
  "model_name": "logistic_regression"
}
```

Supported `task` values: `classification`, `regression`

Supported `model_name` values:

- `logistic_regression`
- `random_forest_classifier`
- `linear_regression`
- `random_forest_regressor`

### Real-data training results

Trained on Symbol: `^NSEI`, Date range: `2024-01-01` → `2024-06-30`

| Model | Task | Target | Training Rows | Validation Rows | Test Rows | Features |
|-------|------|--------|--------------|-----------------|-----------|----------|
| Logistic Regression | classification | next_day_direction | 79 | 17 | 18 | 31 |
| Random Forest Classifier | classification | next_day_direction | 79 | 17 | 18 | 31 |
| Linear Regression | regression | next_day_return | 79 | 17 | 18 | 31 |
| Random Forest Regressor | regression | next_day_return | 79 | 17 | 18 | 31 |

All four models train successfully. No performance conclusions are made in Phase 9.

### Leakage prevention

- Target column is excluded from features
- Chronological Phase 8 splits are reused
- Preprocessing scaler is fitted only on training data
- Test set remains unseen

---

## Phase 10 — Model Evaluation

Phase 10 evaluates the four baseline models trained in Phase 9 using the validation and test splits.

### Pre-evaluation fix: row-count discrepancy

Phase 8 originally reported 79 training rows. Phase 9 initially reported 77 because `get_splits()` independently dropped NaN feature rows after splitting, while `prepare_dataset()` did not. This was fixed by making `get_splits()` reuse `prepare_dataset()` as the single canonical dataset path. Both now consistently report 79 training rows.

### What it does

It re-trains each model on the canonical Phase 8 dataset and evaluates it on:

- Validation split (17 samples)
- Test split (18 samples)

### Classification metrics

- Accuracy
- Precision
- Recall
- F1 Score
- ROC-AUC (when both classes are present)
- Confusion Matrix (TN, FP, FN, TP)
- Class distribution
- Majority-class baseline

### Regression metrics

- MAE
- RMSE
- R²
- Historical mean baseline

### Evaluation API

```http
POST /api/models/evaluate
```

Example request:

```json
{
  "model_run_id": 1,
  "evaluation_split": "test"
}
```

Supported `evaluation_split` values: `validation`, `test`

### Real-data evaluation results

Evaluated on Symbol: `^NSEI`, Date range: `2024-01-01` → `2024-06-30`

**Classification — Validation**

| Model | Samples | Accuracy | Precision | Recall | F1 | ROC-AUC |
|-------|--------:|---------:|----------:|-------:|---:|--------:|
| Logistic Regression | 17 | 0.3529 | 0.4000 | 0.2000 | 0.2667 | 0.4286 |
| Random Forest Classifier | 17 | 0.4118 | 0.5000 | 0.4000 | 0.4444 | 0.3857 |

**Classification — Test**

| Model | Samples | Accuracy | Precision | Recall | F1 | ROC-AUC |
|-------|--------:|---------:|----------:|-------:|---:|--------:|
| Logistic Regression | 18 | 0.6111 | 0.8000 | 0.6154 | 0.6957 | 0.6615 |
| Random Forest Classifier | 18 | 0.7778 | 1.0000 | 0.6923 | 0.8182 | 0.7538 |

**Regression — Validation**

| Model | Samples | MAE | RMSE | R² |
|-------|--------:|----:|-----:|---:|
| Linear Regression | 17 | 0.0085 | 0.0117 | -0.2972 |
| Random Forest Regressor | 17 | 0.0067 | 0.0107 | -0.0959 |

**Regression — Test**

| Model | Samples | MAE | RMSE | R² |
|-------|--------:|----:|-----:|---:|
| Linear Regression | 18 | 0.0102 | 0.0165 | 0.0799 |
| Random Forest Regressor | 18 | 0.0092 | 0.0170 | 0.0132 |

**Classification class distribution**

| Split | Class 0 | Class 1 |
|-------|--------:|--------:|
| Validation | 7 (41.2%) | 10 (58.8%) |
| Test | 5 (27.8%) | 13 (72.2%) |

**Baselines**

- Classification majority-class baseline: 58.8% (validation), 72.2% (test)
- Regression mean-return baseline MAE: 0.0066 (validation), 0.0087 (test)

### Limitations

- Only 114 observations total
- Only 18 test observations
- No hyperparameter tuning
- No model selection based on test results
- Metrics are sample-specific and do not guarantee future performance
- Google Trends correlation does not establish causation

---

## Phase 11 — Prediction API

Phase 11 adds a prediction API that loads a previously trained model and generates predictions from historical feature data.

### Model persistence

Trained models are persisted using `joblib` under:

```
backend/artifacts/models/model_run_<id>.joblib
```

The database `model_runs` table stores the artifact path in the `artifact_path` column. The `.gitignore` excludes the `artifacts/` directory, so model binaries are not committed to Git.

### Prediction flow

1. Client sends `POST /api/models/predict` with `model_run_id`, `symbol`, and `prediction_date`
2. API loads the `model_runs` record
3. Verifies symbol matches the trained model
4. Loads the persisted joblib artifact
5. Retrieves the engineered feature row for the requested date
6. Constructs the feature vector using the exact feature order from training
7. Runs inference without retraining or refitting preprocessing
8. Returns the prediction

### Classification prediction

For `logistic_regression` and `random_forest_classifier`, the API returns:

- `predicted_class`: `0` or `1`
- `predicted_direction`: `Down` or `Up`
- `probability_down` / `probability_up`: class probabilities when available

### Regression prediction

For `linear_regression` and `random_forest_regressor`, the API returns:

- `predicted_return`: predicted next-day return

### Prediction API

```http
POST /api/models/predict
```

Example request:

```json
{
  "model_run_id": 1,
  "symbol": "^NSEI",
  "prediction_date": "2024-06-27"
}
```

### Feature-date semantics

The feature row on date `D` contains information available up to date `D`. The model predicts `next_day_return` or `next_day_direction` for the following market observation. The API does not expose the actual target as the prediction.

### Leakage protection

- Prediction never retrains the model
- Prediction never refits preprocessing/scalers
- Prediction uses only the requested date's feature row
- Future information is never used
- The test set is never modified

### Limitations

- Predictions are available only for dates with existing engineered features
- This is a historical prediction API, not a live trading system
- Future prediction would require ingesting current market and Google Trends data first
- No profitability or investment recommendations are provided

---

## Future Improvements

- SHAP explainability for model predictions
- Model versioning with MLflow
- Scheduled data ingestion with Celery
- Redis caching for API responses
- Additional indices (NIFTY Bank, NIFTY IT)
- Sentiment analysis from financial news
- LSTM/Transformer comparison
- GitHub Actions CI/CD
- Cloud deployment

---

## License

MIT
