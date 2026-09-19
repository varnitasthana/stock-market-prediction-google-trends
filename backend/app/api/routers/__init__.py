from fastapi import APIRouter

from app.api.routers import (
    dashboard,
    features,
    market_data,
    models,
    predictions,
    search_terms,
    trends,
)

router = APIRouter()

router.include_router(search_terms.router)
router.include_router(market_data.router)
router.include_router(trends.router)
router.include_router(features.router)
router.include_router(models.router)
router.include_router(predictions.router)
router.include_router(dashboard.router)
