"""
Seed database with sample data for testing all features
This script creates clean, realistic data for the dashboard
"""
import asyncio
from datetime import date, timedelta
import random
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pandas as pd
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.ext.asyncio import async_sessionmaker

from app.core.config import get_settings
from app.models.database import Base, SearchTerm, MarketData, TrendsData, EngineeredFeature
from app.pipeline.market_pipeline import MarketIngestionService
from app.pipeline.trends_pipeline import TrendsIngestionService
from app.services.feature_engineering_service import FeatureEngineeringService

settings = get_settings()

async def clear_database(session: AsyncSession):
    """Clear all data from tables"""
    print("🧹 Clearing existing data...")
    await session.execute("DELETE FROM engineered_features")
    await session.execute("DELETE FROM trends_data")
    await session.execute("DELETE FROM market_data")
    await session.execute("DELETE FROM search_terms")
    await session.commit()
    print("✅ Database cleared")

async def seed_search_terms(session: AsyncSession) -> list:
    """Create search terms"""
    print("\n📝 Creating search terms...")
    terms = [
        SearchTerm(term="stock market", category="finance", active=True),
        SearchTerm(term="nifty 50", category="indices", active=True),
        SearchTerm(term="sensex", category="indices", active=True),
        SearchTerm(term="share price", category="finance", active=True),
        SearchTerm(term="mutual funds", category="investment", active=True),
    ]
    session.add_all(terms)
    await session.commit()
    
    # Refresh to get IDs
    for term in terms:
        await session.refresh(term)
    
    print(f"✅ Created {len(terms)} search terms")
    return terms

async def seed_market_data(session: AsyncSession):
    """Fetch real market data using yfinance"""
    print("\n📈 Fetching real market data from yfinance...")
    
    symbol = "^NSEI"
    end_date = date.today()
    start_date = end_date - timedelta(days=90)  # Last 90 days
    
    service = MarketIngestionService(session)
    
    try:
        result = await service.ingest(
            symbol=symbol,
            start_date=start_date.isoformat(),
            end_date=end_date.isoformat()
        )
        print(f"✅ Fetched {result['inserted']} market data records for {symbol}")
        return result
    except Exception as e:
        print(f"⚠️ Could not fetch live data: {e}")
        print("📊 Creating sample market data instead...")
        
        # Create sample data if yfinance fails
        current_date = start_date
        base_price = 19500.0
        records = []
        
        while current_date <= end_date:
            if current_date.weekday() < 5:  # Monday to Friday
                daily_change = random.uniform(-2, 2) / 100
                base_price *= (1 + daily_change)
                
                open_price = base_price * (1 + random.uniform(-0.005, 0.005))
                high_price = base_price * (1 + random.uniform(0, 0.01))
                low_price = base_price * (1 - random.uniform(0, 0.01))
                close_price = base_price
                volume = int(random.uniform(200000000, 400000000))
                
                market_record = MarketData(
                    symbol=symbol,
                    date=current_date,
                    open=open_price,
                    high=high_price,
                    low=low_price,
                    close=close_price,
                    adj_close=close_price,
                    volume=volume
                )
                records.append(market_record)
            
            current_date += timedelta(days=1)
        
        session.add_all(records)
        await session.commit()
        print(f"✅ Created {len(records)} sample market data records")

async def seed_trends_data(session: AsyncSession, search_terms: list):
    """Create trends data for search terms"""
    print("\n🔍 Creating Google Trends data...")
    
    end_date = date.today()
    start_date = end_date - timedelta(days=90)
    
    # Get all market dates
    from sqlalchemy import select
    result = await session.execute(
        select(MarketData.date)
        .where(MarketData.symbol == "^NSEI")
        .order_by(MarketData.date)
    )
    market_dates = [row[0] for row in result.fetchall()]
    
    records = []
    for term in search_terms:
        base_interest = random.randint(40, 80)
        for market_date in market_dates:
            # Create realistic trends with some correlation to term
            interest = base_interest + random.randint(-15, 15)
            interest = max(10, min(100, interest))  # Keep between 10-100
            
            trend_record = TrendsData(
                search_term_id=term.id,
                date=market_date,
                interest_score=interest
            )
            records.append(trend_record)
    
    session.add_all(records)
    await session.commit()
    print(f"✅ Created {len(records)} trends data records")

async def generate_features(session: AsyncSession):
    """Generate engineered features"""
    print("\n⚙️ Generating engineered features...")
    
    symbol = "^NSEI"
    end_date = date.today()
    start_date = end_date - timedelta(days=90)
    
    service = FeatureEngineeringService(session)
    
    try:
        result = await service.generate_features_for_symbol(
            symbol=symbol,
            start_date=start_date,
            end_date=end_date
        )
        print(f"✅ Generated {result['total_features']} engineered features")
        print(f"   - Feature names: {result['feature_count']}")
        print(f"   - Date range: {result['date_range']}")
        return result
    except Exception as e:
        print(f"⚠️ Error generating features: {e}")
        import traceback
        traceback.print_exc()

async def verify_data(session: AsyncSession):
    """Verify seeded data"""
    print("\n🔍 Verifying seeded data...")
    
    from sqlalchemy import select, func
    
    # Count records
    counts = {}
    for model, name in [
        (SearchTerm, "search_terms"),
        (MarketData, "market_data"),
        (TrendsData, "trends_data"),
        (EngineeredFeature, "engineered_features")
    ]:
        result = await session.execute(select(func.count()).select_from(model))
        counts[name] = result.scalar()
    
    print("\n📊 Database Summary:")
    print(f"   - Search Terms: {counts['search_terms']}")
    print(f"   - Market Data: {counts['market_data']}")
    print(f"   - Trends Data: {counts['trends_data']}")
    print(f"   - Engineered Features: {counts['engineered_features']}")
    
    # Show date range
    result = await session.execute(
        select(func.min(MarketData.date), func.max(MarketData.date))
        .where(MarketData.symbol == "^NSEI")
    )
    min_date, max_date = result.one()
    print(f"\n📅 Data Range: {min_date} to {max_date}")
    
    return counts

async def main():
    """Main seeding function"""
    print("=" * 60)
    print("🌱 SEEDING DATABASE WITH SAMPLE DATA")
    print("=" * 60)
    
    # Create async engine
    engine = create_async_engine(settings.database_url.replace("postgresql://", "postgresql+asyncpg://"))
    async_session_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session_maker() as session:
        # Step 1: Clear existing data
        await clear_database(session)
        
        # Step 2: Create search terms
        search_terms = await seed_search_terms(session)
        
        # Step 3: Fetch/create market data
        await seed_market_data(session)
        
        # Step 4: Create trends data
        await seed_trends_data(session, search_terms)
        
        # Step 5: Generate features
        await generate_features(session)
        
        # Step 6: Verify data
        counts = await verify_data(session)
    
    await engine.dispose()
    
    print("\n" + "=" * 60)
    print("✅ DATABASE SEEDING COMPLETED SUCCESSFULLY!")
    print("=" * 60)
    print("\n🚀 You can now:")
    print("   1. View data at http://localhost:8000/api/docs")
    print("   2. Open frontend at http://localhost:5173")
    print("   3. Train models using the data")
    print("   4. View statistics and correlations")
    print("\n")

if __name__ == "__main__":
    asyncio.run(main())
