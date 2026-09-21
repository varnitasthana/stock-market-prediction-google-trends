from celery import Celery
from celery.schedules import crontab

from app.core.config import get_settings

settings = get_settings()

app = Celery(
    "stock-prediction-worker",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
)

app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,
    task_soft_time_limit=29 * 60,
)

app.conf.beat_schedule = {
    "ingest-market-data-daily": {
        "task": "app.workers.scheduled_tasks.daily_market_ingestion",
        "schedule": crontab(hour=18, minute=0),
        "args": (),
    },
    "ingest-trends-daily": {
        "task": "app.workers.scheduled_tasks.daily_trends_ingestion",
        "schedule": crontab(hour=18, minute=30),
        "args": (),
    },
    "ingest-sentiment-daily": {
        "task": "app.workers.scheduled_tasks.daily_sentiment_ingestion",
        "schedule": crontab(hour=19, minute=0),
        "args": (),
    },
    "generate-features-daily": {
        "task": "app.workers.scheduled_tasks.daily_feature_generation",
        "schedule": crontab(hour=19, minute=30),
        "args": (),
    },
}

app.conf.task_routes = {
    "app.workers.scheduled_tasks.*": {"queue": "ingestion"},
    "app.workers.ml_tasks.*": {"queue": "ml"},
}
