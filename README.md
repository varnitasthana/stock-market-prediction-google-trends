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
| GET | `/api/search-terms` | List search terms |
| POST | `/api/search-terms` | Add search term |
| GET | `/api/trends` | Get trends data |
| GET | `/api/market-data` | Get market data |
| GET | `/api/features` | Get engineered features |
| POST | `/api/train` | Train a model |
| GET | `/api/models` | List models |
| POST | `/api/predict` | Generate prediction |
| GET | `/api/dashboard/summary` | Dashboard summary |

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
