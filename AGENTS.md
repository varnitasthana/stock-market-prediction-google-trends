# AGENTS.md - Stock Market Prediction Through Google Trends

## Project Overview
Stock market prediction system using Google Trends data for the Indian stock market (NSE).

## Project Structure
- `backend/` - FastAPI backend application
- `frontend/` - React/Vite frontend application

## Environment
- Python 3.14 (TensorFlow/SHAP/MLflow not available for 3.14)
- Node.js project with Vite frontend

## Commands

### Backend
```bash
cd backend
.venv\Scripts\Activate.ps1    # Activate virtual environment
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload  # Start dev server
pytest -q                    # Run tests (108 tests)
ruff check .                  # Lint check
```

### Frontend
```bash
cd frontend
npm install                   # Install dependencies
npm run dev                   # Start dev server (port 5173)
npm run build                 # Build for production
```

## Database
- PostgreSQL running on localhost:5432
- Database name: stock_prediction
- Connection string: postgresql://postgres:postgres@localhost:5432/stock_prediction

## Ports
- Backend API: http://localhost:8000
- Frontend dev: http://localhost:5173
- Swagger docs: http://localhost:8000/api/docs
- Redoc docs: http://localhost:8000/api/redoc

## Key Endpoints
- `GET /api/health` - Health check
- `GET /api/models/` - List all models
- `GET /api/models/{id}/explain` - Model explainability (SHAP)
- `POST /api/sentiment/text` - Sentiment analysis
- `GET /api/market-data/symbols` - List available symbols
- `GET /api/market-data/status/{symbol}` - Data freshness status
- `GET /api/market-data/recent/{symbol}` - Recent market data
- `GET /api/market-data/live/{symbol}` - Latest quote
- `POST /api/market-data/refresh` - Refresh market data
- `GET /api/search-terms/` - Search terms management
- `GET /api/trends/` - Google Trends data
- `GET /api/predictions/` - Model predictions

## Testing
- Run all tests: `pytest -q` (expected: 108 tests passing)
- Lint: `ruff check .` (expected: no issues)
- Frontend build: `npm run build` (from frontend directory)

## Current Status
- All 108 tests pass
- Backend and frontend running on localhost
- Data available from 2024-01-01 to 2026-09-18 (2 sessions behind)
- Models trained on ^NSEI data (training period 2024-01-08 to 2024-05-07)
