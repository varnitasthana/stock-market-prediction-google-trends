# Stock Market Behaviour Prediction System Using Google Trends

## Phase 1 — Requirements, System Architecture & Database Design

This document defines the complete technical blueprint for building the system.

---

## 1. Project Requirements

### 1.1 Problem Statement

The system investigates whether changes in Google search interest for finance-related keywords serve as early indicators of subsequent stock-market behaviour for NIFTY 50 and SENSEX.

### 1.2 Functional Requirements

| ID | Requirement | Description |
|----|-------------|-------------|
| FR-01 | Market Data Ingestion | Collect OHLCV data for NIFTY 50 and SENSEX via `yfinance` |
| FR-02 | Google Trends Ingestion | Collect normalized search-interest data for configurable keywords via `pytrends` |
| FR-03 | Data Validation | Detect missing values, duplicates, outliers, and gaps |
| FR-04 | Data Alignment | Join market and search data on trading dates only |
| FR-05 | Feature Engineering | Generate market, search, and lagged features |
| FR-06 | Statistical Analysis | Compute Pearson, Spearman, cross-correlation, and lagged correlation |
| FR-07 | Feature Selection | Identify statistically useful features |
| FR-08 | ML Training | Train classification (direction) and regression (return) models |
| FR-09 | Time-Series Evaluation | Chronological train/validation/test splits with walk-forward validation |
| FR-10 | Prediction API | REST endpoint for generating predictions |
| FR-11 | Dashboard | React/TypeScript frontend for visualization and prediction |
| FR-12 | Database | PostgreSQL persistence for all data, features, models, and predictions |
| FR-13 | Logging & Monitoring | Structured logging for pipeline, API, and ML events |
| FR-14 | Testing | Unit and integration tests with pytest |
| FR-15 | Docker Support | Containerized backend, frontend, and PostgreSQL |
| FR-16 | Error Handling | Graceful handling of API failures, data gaps, and invalid inputs |

### 1.3 Non-Functional Requirements

| ID | Requirement | Target |
|----|-------------|--------|
| NFR-01 | Performance | API p95 latency < 200ms |
| NFR-02 | Availability | 99.9% uptime for local deployment |
| NFR-03 | Reproducibility | Pinned dependencies and documented setup |
| NFR-04 | Maintainability | Layered architecture with clear separation of concerns |
| NFR-05 | Testability | Minimum 80% unit-test coverage |
| NFR-06 | Scalability | Modular design supports additional indices and keywords without core changes |
| NFR-07 | Security | No secrets in Git, environment-based configuration, CORS restrictions |
| NFR-08 | Documentation | README, inline docstrings, API auto-docs via Swagger |

---

## 2. High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              USER / ANALYST                                  │
└───────────────────────────────────┬─────────────────────────────────────────┘
                                    │
                    ┌───────────────┴───────────────┐
                    │                               │
            ┌───────▼────────┐            ┌────────▼────────┐
            │  React Dashboard│            │  REST API (FastAPI) │
            │  (Port 5173)    │            │  (Port 8000)     │
            └────────────────┘            └────────┬────────┘
                                                   │
                                        ┌──────────▼──────────┐
                                        │   FastAPI App       │
                                        │  (main.py, routers) │
                                        └──────────┬──────────┘
                    ┌───────────────────────────┼───────────────────────────┐
                    │                           │                           │
            ┌───────▼────────┐          ┌──────▼────────┐        ┌───────▼────────┐
            │  API Routers   │          │   Services    │        │  Repositories  │
            │  (search-terms,│          │  (business    │        │  (SQLAlchemy)  │
            │   market, ML)  │          │   logic)      │        │                │
            └────────────────┘          └───────────────┘        └───────┬────────┘
                                                                          │
                    ┌─────────────────────────────────────────────────────┘
                    │
            ┌───────▼──────────────────────┐
            │    ML / Pipeline Layer        │
            │  (ingestion, features,        │
            │   training, evaluation)       │
            └───────┬──────────────────────┘
                    │
        ┌───────────┼───────────────┐
        │           │               │
  ┌────▼────┐  ┌───▼─────┐  ┌────▼────────────┐
  │ yfinance│  │ pytrends│  │  PostgreSQL DB  │
  │(market) │  │(search) │  │  (raw + features)│
  └─────────┘  └─────────┘  └─────────────────┘
```

### 2.1 Component Responsibilities

| Layer | Component | Responsibility |
|-------|-----------|----------------|
| API | `api/routers/*.py` | HTTP request routing, validation, response serialization |
| API | `schemas/*.py` | Pydantic request/response DTOs |
| Services | `services/*.py` | Business logic, orchestration |
| Repositories | `repositories/*.py` | Database CRUD operations via SQLAlchemy |
| ML | `ml/*.py` | Feature engineering, model training, evaluation, prediction |
| Pipeline | `pipeline/*.py` | ETL orchestration for market and trends data |
| Models | `models/*.py` | SQLAlchemy ORM models |
| Core | `core/*.py` | Configuration, database engine, logging setup |
| Utils | `utils/*.py` | Shared helpers (date utilities, data validators) |

### 2.2 Data Flow

```
[1] yfinance → [2] MarketIngestionService → [3] Validation → [4] DB (market_data)
                                                                      │
[5] pytrends → [6] TrendsIngestionService → [7] Validation → [8] DB (trends_data, search_terms)
                                                                      │
[9] FeatureEngineer → [10] Validation → [11] DB (engineered_features)
                                                                      │
[12] StatisticalAnalyzer → Correlation matrices, lag analysis
                                                                      │
[13] ModelTrainer → Walk-forward splits → Training → Evaluation → Model artifacts
                                                                      │
[14] PredictionService → Prediction API → DB (predictions, model_runs)
                                                                      │
[15] Dashboard ← API
```

---

## 3. Technology Stack & Justification

| Technology | Role | Justification |
|------------|------|---------------|
| **Python 3.12+** | Backend language | Latest stable, async support, typing improvements |
| **FastAPI** | Web framework | Async, type-safe, auto-generated OpenAPI docs, high performance |
| **Pydantic v2** | Validation | Data validation, settings management, serialization |
| **SQLAlchemy 2.0** | ORM | Mature, async support, well-documented, flexible |
| **PostgreSQL** | Database | ACID compliance, JSON support, production-grade, good time-series characteristics |
| **Pandas / NumPy** | Data processing | Industry standard for tabular data manipulation |
| **scikit-learn** | ML baseline | Simple, interpretable models, extensive metrics |
| **XGBoost** | Advanced ML | Gradient boosting, handles non-linearities, feature importance |
| **pytrends** | Google Trends API | Unofficial but reliable Python client for Google Trends |
| **yfinance** | Market data | Free, reliable OHLCV data for NIFTY/SENSEX proxies |
| **scipy** | Statistics | Correlation functions, statistical tests |
| **React + TypeScript + Vite** | Frontend | Modern, type-safe, fast dev experience |
| **Tailwind CSS** | Styling | Utility-first, rapid UI development |
| **Recharts** | Charts | React-native charting, good for financial data |
| **Docker + Compose** | Deployment | Consistent local and production environments |
| **pytest** | Testing | Industry-standard Python test framework |
| **Ruff** | Linting | Fast Python linter, replaces flake8/black/isort |

---

## 4. Database Design

### 4.1 Entity-Relationship Diagram

```
┌─────────────────┐       ┌──────────────────────┐
│   search_terms  │       │     market_data      │
├─────────────────┤       ├──────────────────────┤
│ id (PK)         │       │ id (PK)              │
│ term (UNIQUE)   │       │ symbol               │
│ category        │       │ date                 │
│ active          │       │ open, high, low, close│
│ created_at      │       │ volume               │
└────────┬────────┘       │ daily_return         │
         │                │ volatility           │
         │                └──────────────────────┘
         │ 1:N
┌────────▼─────────────────┐
│     trends_data          │
├──────────────────────────┤
│ id (PK)                  │
│ search_term_id (FK)      │
│ date                     │
│ interest_score           │
│ UNIQUE(search_term_id, date) │
└──────────────────────────┘

┌──────────────────────────┐       ┌──────────────────────┐
│   engineered_features    │       │     model_runs       │
├──────────────────────────┤       ├──────────────────────┤
│ id (PK)                  │       │ id (PK)              │
│ symbol                   │       │ model_name           │
│ date                     │       │ symbol               │
│ feature_name             │       │ training_start/end   │
│ feature_value            │       │ evaluation_start/end │
│ UNIQUE(symbol, date,     │       │ metrics (JSON)       │
│   feature_name)          │       │ created_at           │
└──────────────────────────┘       └──────────┬───────────┘
                                             │ 1:N
                                    ┌────────▼──────────────────┐
                                    │       predictions         │
                                    ├───────────────────────────┤
                                    │ id (PK)                   │
                                    │ model_run_id (FK)         │
                                    │ symbol                    │
                                    │ prediction_date           │
                                    │ predicted_return          │
                                    │ predicted_direction       │
                                    │ probability               │
                                    │ actual_return             │
                                    │ actual_direction          │
                                    └───────────────────────────┘
```

### 4.2 Table Definitions

#### `search_terms`
Stores configured financial search terms.

```sql
CREATE TABLE search_terms (
    id SERIAL PRIMARY KEY,
    term VARCHAR(255) UNIQUE NOT NULL,
    category VARCHAR(100) DEFAULT 'general',
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW()
);
```

#### `market_data`
Stores OHLCV data for market indices.

```sql
CREATE TABLE market_data (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(50) NOT NULL,
    date DATE NOT NULL,
    open NUMERIC,
    high NUMERIC,
    low NUMERIC,
    close NUMERIC,
    adj_close NUMERIC,
    volume BIGINT,
    daily_return NUMERIC,
    volatility NUMERIC,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(symbol, date)
);
CREATE INDEX idx_market_data_symbol_date ON market_data(symbol, date);
```

#### `trends_data`
Stores Google Trends interest scores.

```sql
CREATE TABLE trends_data (
    id SERIAL PRIMARY KEY,
    search_term_id INTEGER REFERENCES search_terms(id) ON DELETE CASCADE,
    date DATE NOT NULL,
    interest_score INTEGER,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(search_term_id, date)
);
CREATE INDEX idx_trends_data_term_date ON trends_data(search_term_id, date);
```

#### `engineered_features`
Stores computed features for ML.

```sql
CREATE TABLE engineered_features (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(50) NOT NULL,
    date DATE NOT NULL,
    feature_name VARCHAR(255) NOT NULL,
    feature_value NUMERIC,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(symbol, date, feature_name)
);
CREATE INDEX idx_engineered_features_symbol_date ON engineered_features(symbol, date);
```

#### `model_runs`
Stores metadata for each training run.

```sql
CREATE TABLE model_runs (
    id SERIAL PRIMARY KEY,
    model_name VARCHAR(100) NOT NULL,
    symbol VARCHAR(50) NOT NULL,
    training_start DATE NOT NULL,
    training_end DATE NOT NULL,
    evaluation_start DATE NOT NULL,
    evaluation_end DATE NOT NULL,
    metrics JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);
```

#### `predictions`
Stores prediction results.

```sql
CREATE TABLE predictions (
    id SERIAL PRIMARY KEY,
    model_run_id INTEGER REFERENCES model_runs(id) ON DELETE CASCADE,
    symbol VARCHAR(50) NOT NULL,
    prediction_date DATE NOT NULL,
    predicted_return NUMERIC,
    predicted_direction INTEGER,
    probability NUMERIC,
    actual_return NUMERIC,
    actual_direction INTEGER,
    created_at TIMESTAMP DEFAULT NOW()
);
```

---

## 5. API Design

### 5.1 Endpoint Summary

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/health` | Health check |
| GET | `/api/search-terms` | List all search terms |
| POST | `/api/search-terms` | Add a search term |
| GET | `/api/search-terms/{id}` | Get specific search term |
| DELETE | `/api/search-terms/{id}` | Remove search term |
| GET | `/api/trends` | Get trends data (with filters) |
| POST | `/api/trends/ingest` | Trigger trends ingestion |
| GET | `/api/market-data` | Get market data (with filters) |
| POST | `/api/market-data/ingest` | Trigger market data ingestion |
| GET | `/api/correlation` | Get correlation analysis |
| GET | `/api/features` | Get engineered features |
| POST | `/api/train` | Train a model |
| GET | `/api/models` | List trained models |
| GET | `/api/models/{id}` | Get model details |
| POST | `/api/predict` | Generate prediction |
| GET | `/api/predictions` | List predictions |
| GET | `/api/dashboard/summary` | Dashboard summary data |

### 5.2 Request/Response Examples

#### Search Term
```json
POST /api/search-terms
{
  "term": "recession",
  "category": "macro"
}

Response 201:
{
  "id": 1,
  "term": "recession",
  "category": "macro",
  "active": true,
  "created_at": "2026-09-17T18:00:00Z"
}
```

#### Model Training
```json
POST /api/train
{
  "model_name": "random_forest",
  "symbol": "NSEI",
  "target": "direction",
  "training_start": "2018-01-01",
  "training_end": "2023-12-31",
  "validation_end": "2024-12-31"
}
```

---

## 6. Folder Structure

```
stock-market-behaviour-prediction/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                    # FastAPI app entrypoint
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   ├── deps.py                # Shared dependencies (DB session, etc.)
│   │   │   └── routers/
│   │   │       ├── __init__.py
│   │   │       ├── search_terms.py
│   │   │       ├── market_data.py
│   │   │       ├── trends.py
│   │   │       ├── features.py
│   │   │       ├── models.py
│   │   │       ├── predictions.py
│   │   │       └── dashboard.py
│   │   ├── core/
│   │   │   ├── __init__.py
│   │   │   ├── config.py              # Settings via Pydantic Settings
│   │   │   ├── database.py            # SQLAlchemy engine & session
│   │   │   └── logging.py             # Structured logging setup
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   └── database.py            # SQLAlchemy ORM models
│   │   ├── schemas/
│   │   │   ├── __init__.py
│   │   │   ├── search_terms.py
│   │   │   ├── market_data.py
│   │   │   ├── trends.py
│   │   │   ├── features.py
│   │   │   ├── models.py
│   │   │   ├── predictions.py
│   │   │   └── common.py
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── search_term_service.py
│   │   │   ├── market_data_service.py
│   │   │   ├── trends_service.py
│   │   │   ├── feature_service.py
│   │   │   ├── model_service.py
│   │   │   ├── prediction_service.py
│   │   │   └── dashboard_service.py
│   │   ├── repositories/
│   │   │   ├── __init__.py
│   │   │   ├── search_term_repo.py
│   │   │   ├── market_data_repo.py
│   │   │   ├── trends_repo.py
│   │   │   ├── features_repo.py
│   │   │   ├── model_repo.py
│   │   │   └── prediction_repo.py
│   │   ├── ml/
│   │   │   ├── __init__.py
│   │   │   ├── feature_engineer.py
│   │   │   ├── statistical_analyzer.py
│   │   │   ├── model_trainer.py
│   │   │   ├── evaluator.py
│   │   │   ├── predictor.py
│   │   │   └── schemas.py
│   │   ├── pipeline/
│   │   │   ├── __init__.py
│   │   │   ├── market_pipeline.py
│   │   │   ├── trends_pipeline.py
│   │   │   ├── feature_pipeline.py
│   │   │   └── run.py                  # Entry point: python -m app.pipeline.run
│   │   └── utils/
│   │       ├── __init__.py
│   │       ├── dates.py
│   │       ├── validators.py
│   │       └── io.py
│   ├── tests/
│   │   ├── __init__.py
│   │   ├── conftest.py
│   │   ├── test_validators.py
│   │   ├── test_feature_engineer.py
│   │   ├── test_statistical_analyzer.py
│   │   ├── test_repositories.py
│   │   ├── test_api_search_terms.py
│   │   ├── test_api_market.py
│   │   ├── test_api_trends.py
│   │   ├── test_pipeline.py
│   │   └── test_model_trainer.py
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── main.tsx
│   │   ├── App.tsx
│   │   ├── index.css
│   │   ├── vite-env.d.ts
│   │   ├── types/
│   │   │   └── index.ts
│   │   ├── services/
│   │   │   └── api.ts
│   │   ├── hooks/
│   │   │   └── useApi.ts
│   │   ├── components/
│   │   │   ├── Layout.tsx
│   │   │   ├── Sidebar.tsx
│   │   │   ├── MarketChart.tsx
│   │   │   ├── TrendsChart.tsx
│   │   │   ├── CorrelationTable.tsx
│   │   │   ├── PredictionCard.tsx
│   │   │   ├── ModelEvaluation.tsx
│   │   │   ├── FeatureImportance.tsx
│   │   │   └── Loader.tsx
│   │   └── pages/
│   │       ├── Dashboard.tsx
│   │       ├── MarketAnalysis.tsx
│   │       ├── TrendsAnalysis.tsx
│   │       ├── ModelTraining.tsx
│   │       └── Predictions.tsx
│   ├── package.json
│   ├── tsconfig.json
│   ├── vite.config.ts
│   ├── tailwind.config.ts
│   ├── postcss.config.js
│   ├── index.html
│   ├── public/
│   │   └── favicon.ico
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

## 7. Configuration Design

### 7.1 Environment Variables

```env
# Application
APP_NAME="Stock Market Prediction System"
API_ENV=development
LOG_LEVEL=INFO
SECRET_KEY=change-me-in-production

# Database
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/stock_prediction

# External APIs
PYTRENDS_RETRIES=3
PYTRENDS_SLEEP=1

# Data
DEFAULT_MARKET_SYMBOL=NSEI
DEFAULT_START_DATE=2018-01-01
DEFAULT_END_DATE=2025-01-01
```

---

## 8. Development Roadmap

| Phase | Name | Deliverable | Status |
|-------|------|-------------|--------|
| 1 | Requirements & Architecture | This document | ✅ Current |
| 2 | Backend Foundation | FastAPI app, DB models, config | Pending |
| 3 | Market Data Pipeline | yfinance ingestion + persistence | Pending |
| 4 | Google Trends Pipeline | pytrends ingestion + persistence | Pending |
| 5 | Data Alignment | Date-aligned merged dataset | Pending |
| 6 | Feature Engineering | Features + lagged variables | Pending |
| 7 | Statistical Analysis | Correlation, lag analysis | Pending |
| 8 | Machine Learning | Baseline through XGBoost | Pending |
| 9 | Time-Series Evaluation | Walk-forward validation, metrics | Pending |
| 10 | Prediction API | Prediction endpoints | Pending |
| 11 | React Dashboard | Full UI | Pending |
| 12 | Testing & Hardening | pytest suite, error handling | Pending |
| 13 | Dockerization | docker-compose up --build | Pending |
| 14 | Documentation | Professional README | Pending |

---

## 9. Key Architectural Decisions

### 9.1 Why FastAPI?
- Native async support for I/O-bound external API calls (yfinance, pytrends)
- Auto-generated Swagger/OpenAPI documentation
- Strong typing with Pydantic reduces runtime errors
- High performance comparable to Node.js and Go

### 9.2 Why PostgreSQL over SQLite?
- Concurrent access support for frontend + pipeline + API
- JSONB support for flexible metrics storage
- Production-ready with proper backup/replication options
- Superior indexing for time-series queries

### 9.3 Why SQLAlchemy 2.0?
- Async support via `asyncpg`
- Clean separation of schema definition and queries
- Mature migration support via Alembic
- Type-safe query construction

### 9.4 Why pytrends?
- Free, no API key required for Google Trends
- Handles session management and rate limiting
- Well-maintained community library

### 9.5 Why yfinance?
- Free, reliable historical data
- Supports NIFTY 50 (^NSEI) and SENSEX (^BSESN)
- No registration required

### 9.6 Why scikit-learn before XGBoost?
- Establishes interpretable baselines
- Prevents premature complexity
- Makes it easier to explain model behavior in interviews

---

## 10. Important Disclaimers

This project is for **research and educational purposes only**.

- Correlation between search behaviour and market movement does not establish causation.
- The system estimates the probability/direction of subsequent market movement based on historical relationships.
- This is NOT investment advice.
- Financial time-series prediction is inherently noisy and non-stationary.
- Past performance does not guarantee future results.
