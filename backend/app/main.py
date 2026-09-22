from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
import time

from app.api.routers import (
    alignment,
    dashboard,
    features,
    market_data,
    ml_dataset,
    models,
    predictions,
    search_terms,
    sentiment,
    statistics,
    trends,
)
from app.core.config import get_settings
from app.core.logging import setup_logging
from app.core.rate_limit import RateLimitMiddleware

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    setup_logging()
    yield
    # Shutdown


app = FastAPI(
    title="Stock Market Prediction System",
    description="Analyzes Google Trends data for stock market behavior prediction.",
    version="0.2.0",
    lifespan=lifespan,
    docs_url="/api/docs" if settings.api_env != "production" else None,
    redoc_url="/api/redoc" if settings.api_env != "production" else None,
)

# Security headers middleware
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response

# Request timing middleware
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response

app.add_middleware(GZipMiddleware, minimum_size=1000)

# Add rate limiting (disabled in test environment)
if settings.api_env != "test":
    app.add_middleware(
        RateLimitMiddleware,
        calls=settings.rate_limit_per_minute,
        period=60
    )

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    allow_headers=["*"],
    max_age=3600,
)


@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    return JSONResponse(
        status_code=400,
        content={"detail": str(exc)},
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )


@app.get("/api/health")
async def health():
    return {"status": "healthy", "service": "stock-prediction-api", "version": "0.2.0"}


app.include_router(search_terms.router, prefix="/api/search-terms", tags=["search-terms"])
app.include_router(market_data.router, prefix="/api/market-data", tags=["market-data"])
app.include_router(trends.router, prefix="/api/trends", tags=["trends"])
app.include_router(alignment.router, prefix="/api/alignment", tags=["alignment"])
app.include_router(features.router, prefix="/api/features", tags=["features"])
app.include_router(statistics.router, prefix="/api/statistics", tags=["statistics"])
app.include_router(ml_dataset.router, prefix="/api/ml-dataset", tags=["ml-dataset"])
app.include_router(models.router, prefix="/api/models", tags=["models"])
app.include_router(predictions.router, prefix="/api/predictions", tags=["predictions"])
app.include_router(dashboard.router, prefix="/api/dashboard", tags=["dashboard"])
app.include_router(sentiment.router, prefix="/api/sentiment", tags=["sentiment"])
