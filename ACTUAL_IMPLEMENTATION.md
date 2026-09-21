# Stock Market Prediction Through Google Trends - Actual Implementation

## Overview
This system analyzes the relationship between Google Trends search interest and stock market behavior for NIFTY 50 (NSE India). It uses machine learning to predict market direction or returns based on historical data.

**Important**: This is a research/educational project. NOT intended for actual trading.

---

## What Actually Works

### ✅ Fully Functional Features

#### 1. Data Ingestion
- **Market Data**: Uses `yfinance` to fetch OHLCV data for ^NSEI (NIFTY 50)
- **Google Trends**: Uses `pytrends` to collect search interest data
- **Retry Logic**: Automatic retries with exponential backoff
- **Deduplication**: Prevents duplicate data insertion

#### 2. Data Pipeline
Complete pipeline from raw data to predictions:
```
Google Trends → Trends Data Table
Market Data (yfinance) → Market Data Table
         ↓
Temporal Alignment (trading days only)
         ↓
Feature Engineering (40+ features)
         ↓
Statistical Analysis (correlations)
         ↓
ML Dataset Creation (train/validation/test splits)
         ↓
Model Training
         ↓
Model Evaluation
         ↓
Predictions with Artifacts
```

#### 3. Feature Engineering
Generates 40+ features including:
- **Market Features**: daily_return, log_return, volatility, momentum, RSI, moving averages
- **Trend Features**: interest_score_change, rolling_mean, rolling_std, lag features
- **Target Variables**: 
  - Classification: next_day_direction (up/down)
  - Regression: next_day_return (actual return %)

**Data Leakage Prevention**: Features use only historical data (no future information)

#### 4. Machine Learning Models

**Working Models** (scikit-learn):
- **Logistic Regression** - Classification with StandardScaler
- **Random Forest Classifier** - Classification
- **Linear Regression** - Regression with StandardScaler
- **Random Forest Regressor** - Regression
- **XGBoost** - Both classification and regression (via scikit-learn API)

**Model Features**:
- Proper train/validation/test chronological splits
- Handles missing values with imputation
- StandardScaler for appropriate models
- Feature importance extraction
- Deterministic results with random_state

#### 5. Evaluation Metrics
- **Classification**: accuracy, precision, recall, F1-score, ROC-AUC, confusion matrix
- **Regression**: MAE, RMSE, R²
- **Baselines**: Majority class baseline (classification), mean baseline (regression)

#### 6. Prediction API
- RESTful FastAPI endpoints
- Model artifact persistence with joblib
- Feature validation before prediction
- SHAP explainability (for sklearn models)
- MLflow experiment tracking (optional, conditional)

#### 7. Background Jobs (Celery)
Scheduled daily tasks:
- Market data ingestion (18:00 UTC)
- Trends data ingestion (18:30 UTC)
- Sentiment ingestion (19:00 UTC)
- Feature generation (19:30 UTC)

#### 8. Frontend
React + TypeScript dashboard with:
- Market data visualization (Recharts)
- Model training interface
- Prediction interface
- Statistical analysis view
- Explainability view

#### 9. Infrastructure
- **Docker Compose**: postgres, redis, backend, celery-worker, celery-beat, mlflow, frontend
- **Database**: PostgreSQL with proper indexes and unique constraints
- **Migrations**: Alembic with 3 migration files
- **API Documentation**: Swagger UI at `/api/docs`

#### 10. Security Features
- CORS middleware with configurable origins
- Security headers (X-Content-Type-Options, X-Frame-Options, XSS-Protection, HSTS)
- Input validation via Pydantic schemas
- SQL injection protection (SQLAlchemy ORM)
- GZip compression
- Rate limiting (in-memory, suitable for local/single-worker deployments)

---

## ⚠️ Optional/Experimental Features

### LSTM & Transformer Models
**Status**: Code exists but **NOT FUNCTIONAL** on Python 3.14

**Reason**: TensorFlow 2.17+ is not available for Python 3.14

**Models Defined but NOT Working**:
- `lstm_classifier`
- `lstm_regressor`
- `transformer_classifier`
- `transformer_regressor`

**To Enable** (requires Python 3.11 or 3.12):
1. Use Python 3.11 or 3.12
2. Uncomment `tensorflow>=2.17.0` in requirements.txt
3. Run `pip install -r requirements.txt`
4. Models will then be available for training

**Code Structure**: The code gracefully handles TensorFlow import failures with try/except blocks, so the application works fine without TensorFlow.

### SHAP Explainability
**Status**: **FUNCTIONAL** for sklearn models

**Works with**: Logistic Regression, Random Forest, XGBoost
**Does NOT work with**: LSTM, Transformer (TensorFlow models)

**Integration**: Conditional in training service:
- Attempts to create SHAP explainer during training
- Saves explainer with model artifact
- Falls back gracefully if SHAP fails

### MLflow Tracking
**Status**: **FUNCTIONAL but OPTIONAL**

**Requires**: 
- MLflow server running (docker-compose includes it on port 5000)
- `MLFLOW_TRACKING_URI` environment variable set

**Features**:
- Logs model parameters
- Logs training metrics
- Saves model artifacts (sklearn models only)
- Wrapped in try/except (continues without MLflow if unavailable)

### Sentiment Analysis
**Status**: **PARTIALLY IMPLEMENTED**

- API endpoints exist (`/api/sentiment/`)
- Service layer exists
- Requires external API key (`SENTIMENT_API_KEY`)
- Not integrated into main ML pipeline

---

## 🚫 What is NOT Implemented

### 1. SENSEX Support
**Claim**: Documentation mentions SENSEX
**Reality**: Only NIFTY 50 (^NSEI) is supported
**Also Supported**: ^NSEBANK (NSE Bank), ^CNXIT (NSE IT)
**To Add SENSEX**: Would need to add ^BSESN to supported_symbols

### 2. Authentication/Authorization
**Status**: NOT implemented
**Security**: API endpoints are completely open
**Suitable for**: Local/research use only
**Not suitable for**: Public deployment

### 3. Pagination
**Status**: NOT implemented
**Impact**: List endpoints return all records
**Works for**: Small-medium datasets
**Needs improvement for**: Large production deployments

### 4. Production-Grade Rate Limiting
**Current**: In-memory storage (defaultdict)
**Limitation**: Per-worker, resets on restart
**Suitable for**: Local development, single-worker deployment
**NOT suitable for**: Multi-worker production (use Redis-backed solution)

### 5. Monitoring/Observability
**Status**: NOT implemented
**Missing**: 
- Prometheus metrics
- Request ID tracking
- Distributed tracing
- Log aggregation
- Performance dashboards

### 6. Comprehensive Test Coverage
**Current**: 108 tests, focuses on core ML pipeline
**Missing**: 
- E2E frontend-backend tests
- Security penetration tests
- Load tests
- Integration tests with external APIs

---

## Architecture (Simple Explanation)

```
┌─────────────────────────────────────────────────────────────────┐
│                        USER / ANALYST                            │
└────────────────────────┬────────────────────────────────────────┘
                         │
         ┌───────────────┴───────────────┐
         │                               │
    ┌────▼─────┐                  ┌────▼────┐
    │ React    │                  │ FastAPI │
    │Dashboard │◄─────────────────┤   API   │
    └──────────┘    REST/JSON     └────┬────┘
                                       │
                    ┌──────────────────┼──────────────────┐
                    │                  │                  │
              ┌─────▼─────┐     ┌─────▼─────┐    ┌─────▼─────┐
              │ Services  │     │  ML       │    │Celery     │
              │ (Business │     │ Pipeline  │    │Background │
              │  Logic)   │     │           │    │Workers    │
              └─────┬─────┘     └─────┬─────┘    └─────┬─────┘
                    │                 │                 │
                    └────────┬────────┴─────────────────┘
                             │
                      ┌──────▼────────┐
                      │  PostgreSQL   │
                      │  (Database)   │
                      └───────────────┘
```

**Layer Responsibilities**:
1. **API (FastAPI)**: HTTP routing, request validation, response formatting
2. **Services**: Business logic, orchestration, ML operations
3. **Repositories**: Database CRUD operations (SQLAlchemy)
4. **ML Pipeline**: Feature engineering, training, evaluation, prediction
5. **Workers**: Background jobs (Celery + Redis)
6. **Database**: PostgreSQL with proper schema and indexes

---

## Technology Stack

### Backend
- **Python 3.14** (Note: Limits TensorFlow availability)
- **FastAPI** - Async web framework
- **SQLAlchemy 2.0** - ORM with asyncpg
- **PostgreSQL 16** - Database
- **Celery** - Background task queue
- **Redis** - Message broker for Celery

### Machine Learning
- **pandas** - Data manipulation
- **numpy** - Numerical computing
- **scikit-learn** - ML models (Logistic Regression, Random Forest)
- **XGBoost** - Gradient boosting
- **scipy** - Statistical functions
- **SHAP** - Model explainability (optional)
- **MLflow** - Experiment tracking (optional)

### Data Sources
- **yfinance** - Stock market data
- **pytrends** - Google Trends data

### Frontend
- **React 18** - UI framework
- **TypeScript** - Type safety
- **Tailwind CSS** - Styling
- **Recharts** - Charts and visualizations
- **TanStack Query** - API state management
- **Vite** - Build tool

### Infrastructure
- **Docker Compose** - Container orchestration
- **Alembic** - Database migrations
- **pytest** - Testing framework

---

## Running the Application

### Prerequisites
- Python 3.11-3.14 (3.11 or 3.12 for TensorFlow support)
- Docker & Docker Compose
- PostgreSQL (if not using Docker)

### Quick Start with Docker
```bash
# Start all services
docker-compose up -d

# Run migrations
docker-compose exec backend alembic upgrade head

# Access API: http://localhost:8000
# Access API docs: http://localhost:8000/api/docs
# Access Frontend: http://localhost:5173
# Access MLflow: http://localhost:5000
```

### Local Development
```bash
# Backend
cd backend
python -m venv .venv
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Linux/Mac
pip install -r requirements.txt

# Set environment variables (copy .env.example to .env)
# Update SECRET_KEY with a 32+ character string

# Run migrations
alembic upgrade head

# Start API
uvicorn app.main:app --reload

# Start Celery worker (separate terminal)
celery -A app.workers.celery_app worker --loglevel=info

# Frontend
cd frontend
npm install
npm run dev
```

### Running Tests
```bash
cd backend
python -m pytest tests/ -v
```

**Test Results**: 108 passed, 0 failed

---

## Database Schema

### Tables
1. **search_terms** - Google search keywords
2. **market_data** - OHLCV stock data (indexed on symbol, date)
3. **trends_data** - Google Trends interest scores (indexed on search_term_id, date)
4. **engineered_features** - Calculated ML features
5. **model_runs** - Model training metadata and artifacts

### Indexes
- `(symbol, date)` on market_data
- `(search_term_id, date)` on trends_data
- `(symbol, date)` on engineered_features

---

## Configuration

### Environment Variables (.env)
```bash
# Required
SECRET_KEY=<32+ character string>
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/stock_prediction

# Optional
MLFLOW_TRACKING_URI=http://localhost:5000
SENTIMENT_API_KEY=<your-api-key>
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/1

# Security
ALLOWED_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
RATE_LIMIT_PER_MINUTE=60
```

---

## Known Limitations

1. **TensorFlow Models**: Not available on Python 3.14
2. **Rate Limiting**: In-memory only, not for multi-worker production
3. **SENSEX**: Mentioned in docs but not actually supported
4. **Authentication**: No auth system implemented
5. **Pagination**: Not implemented, all list endpoints return full results
6. **Single Market**: Primarily designed for NIFTY 50

---

## Future Improvements (Not Currently Implemented)

1. **Authentication**: JWT or API key authentication
2. **Pagination**: Add skip/limit to list endpoints
3. **Redis Rate Limiting**: Shared state across workers
4. **Monitoring**: Prometheus metrics, Grafana dashboards
5. **Additional Markets**: SENSEX, other Indian indices
6. **Enhanced Testing**: E2E, load, security tests
7. **CI/CD**: Automated testing and deployment pipeline

---

## Support

For issues or questions:
1. Check API documentation at `/api/docs`
2. Review logs in Docker containers
3. Check test suite with `pytest tests/ -v`

---

**Last Updated**: 2026-09-21
**Version**: 0.2.0
**Test Status**: ✅ 108 passed
