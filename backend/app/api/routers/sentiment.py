from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.sentiment import SentimentResponse, SentimentTextRequest, SentimentTextResponse
from app.services.sentiment_service import SentimentError, SentimentService

router = APIRouter()


@router.get("/daily/{symbol}", response_model=SentimentResponse)
async def get_daily_sentiment(symbol: str, db: AsyncSession = Depends(get_db)):
    from datetime import date
    service = SentimentService(db)
    try:
        result = await service.ingest_daily_sentiment()
        if result.get("status") == "skipped":
            return SentimentResponse(
                symbol=symbol,
                date=date.today().isoformat(),
                sentiment_score=0.0,
                sentiment_label="neutral",
                source="derived_from_market",
                details=result,
            )
        return SentimentResponse(
            symbol=result["symbol"],
            date=result["date"],
            sentiment_score=result["sentiment_score"],
            sentiment_label=result["sentiment_label"],
            source=result["source"],
        )
    except SentimentError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Sentiment analysis failed: {exc}") from exc


@router.post("/text", response_model=SentimentTextResponse)
async def analyze_sentiment_text(request: SentimentTextRequest):
    service = SentimentService(None)
    result = service.analyze_sentiment_text(request.text)
    return SentimentTextResponse(
        score=result["score"],
        label=result["label"],
        positive_count=result["positive_count"],
        negative_count=result["negative_count"],
    )
