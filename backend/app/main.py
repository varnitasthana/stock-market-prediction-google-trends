from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routers import search_terms, market_data, trends, features, models, predictions, dashboard
from app.core.logging import setup_logging

app = FastAPI(
    title="Stock Market Prediction System",
    description="Analyzes Google Trends data for stock market behavior prediction.",
    version="0.1.0",
)

setup_logging()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
async def health():
    return {"status": "healthy", "service": "stock-prediction-api"}


app.include_router(search_terms.router, prefix="/api/search-terms", tags=["search-terms"])
app.include_router(market_data.router, prefix="/api/market-data", tags=["market-data"])
app.include_router(trends.router, prefix="/api/trends", tags=["trends"])
app.include_router(features.router, prefix="/api/features", tags=["features"])
app.include_router(models.router, prefix="/api/models", tags=["models"])
app.include_router(predictions.router, prefix="/api/predictions", tags=["predictions"])
app.include_router(dashboard.router, prefix="/api/dashboard", tags=["dashboard"])
