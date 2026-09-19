from sqlalchemy import (
    TIMESTAMP,
    BigInteger,
    Boolean,
    Column,
    Date,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
)
from sqlalchemy.sql import func

from app.core.database import Base


class SearchTerm(Base):
    __tablename__ = "search_terms"

    id = Column(Integer, primary_key=True, index=True)
    term = Column(String(255), unique=True, nullable=False)
    category = Column(String(100), default="general")
    active = Column(Boolean, default=True)
    created_at = Column(TIMESTAMP, server_default=func.now())


class MarketData(Base):
    __tablename__ = "market_data"

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(50), nullable=False)
    date = Column(Date, nullable=False)
    open = Column(Numeric)
    high = Column(Numeric)
    low = Column(Numeric)
    close = Column(Numeric)
    adj_close = Column(Numeric)
    volume = Column(BigInteger)
    daily_return = Column(Numeric)
    volatility = Column(Numeric)
    created_at = Column(TIMESTAMP, server_default=func.now())

    __table_args__ = (
        UniqueConstraint("symbol", "date", name="uq_market_data_symbol_date"),
        Index("idx_market_data_symbol_date", "symbol", "date"),
    )


class TrendsData(Base):
    __tablename__ = "trends_data"

    id = Column(Integer, primary_key=True, index=True)
    search_term_id = Column(Integer, ForeignKey("search_terms.id", ondelete="CASCADE"), nullable=False)
    date = Column(Date, nullable=False)
    interest_score = Column(Integer)
    created_at = Column(TIMESTAMP, server_default=func.now())

    __table_args__ = (
        UniqueConstraint("search_term_id", "date", name="uq_trends_data_term_date"),
        Index("idx_trends_data_term_date", "search_term_id", "date"),
    )


class EngineeredFeature(Base):
    __tablename__ = "engineered_features"

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(50), nullable=False)
    date = Column(Date, nullable=False)
    feature_name = Column(String(255), nullable=False)
    feature_value = Column(Numeric)
    created_at = Column(TIMESTAMP, server_default=func.now())

    __table_args__ = (
        UniqueConstraint("symbol", "date", "feature_name", name="uq_engineered_features"),
        Index("idx_engineered_features_symbol_date", "symbol", "date"),
    )


class ModelRun(Base):
    __tablename__ = "model_runs"

    id = Column(Integer, primary_key=True, index=True)
    model_name = Column(String(100), nullable=False)
    symbol = Column(String(50), nullable=False)
    task_type = Column(String(50), nullable=False, default="classification")
    target_name = Column(String(100), nullable=False)
    training_start = Column(Date, nullable=False)
    training_end = Column(Date, nullable=False)
    evaluation_start = Column(Date, nullable=False)
    evaluation_end = Column(Date, nullable=False)
    test_start_date = Column(Date, nullable=True)
    test_end_date = Column(Date, nullable=True)
    parameters = Column(String, nullable=True)
    random_state = Column(Integer, nullable=True)
    feature_count = Column(Integer, nullable=True)
    artifact_path = Column(String(500), nullable=True)
    metrics = Column(String, nullable=True)
    created_at = Column(TIMESTAMP, server_default=func.now())


class Prediction(Base):
    __tablename__ = "predictions"

    id = Column(Integer, primary_key=True, index=True)
    model_run_id = Column(Integer, ForeignKey("model_runs.id", ondelete="CASCADE"), nullable=False)
    symbol = Column(String(50), nullable=False)
    prediction_date = Column(Date, nullable=False)
    predicted_return = Column(Numeric)
    predicted_direction = Column(Integer)
    probability = Column(Numeric)
    actual_return = Column(Numeric)
    actual_direction = Column(Integer)
    created_at = Column(TIMESTAMP, server_default=func.now())
