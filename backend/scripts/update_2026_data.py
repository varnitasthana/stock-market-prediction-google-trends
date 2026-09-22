"""
Fetch fresh 2026 market data and update database
Run this to get latest NIFTY 50 data for 2026
"""
import asyncio
import sys
import os
from datetime import date

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.ext.asyncio import async_sessionmaker

from app.core.config import get_settings
from app.pipeline.market_pipeline import MarketIngestionService

settings = get_settings()

async def update_market_data():
    """Fetch latest 2026 market data"""
    print("=" * 70)
    print("🔄 UPDATING MARKET DATA FOR 2026")
    print("=" * 70)
    
    # Create async engine
    engine = create_async_engine(
        settings.database_url.replace("postgresql://", "postgresql+asyncpg://")
    )
    async_session_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    try:
        async with async_session_maker() as session:
            service = MarketIngestionService(session)
            
            # Fetch data from 2024-01-01 to today (2026-09-21)
            print("\n📊 Fetching NIFTY 50 data from yfinance...")
            print("   Symbol: ^NSEI")
            print("   Start Date: 2024-01-01")
            print(f"   End Date: {date.today()}")
            
            result = await service.ingest(
                symbol="^NSEI",
                start_date="2024-01-01",
                end_date=date.today().isoformat()
            )
            
            print("\n✅ Success!")
            print(f"   Total records fetched: {result['total_records']}")
            print(f"   New records inserted: {result['inserted']}")
            print(f"   Date range: {result['date_range']}")
            
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await engine.dispose()
    
    print("\n" + "=" * 70)
    print("✅ DATA UPDATE COMPLETED!")
    print("=" * 70)
    print("\n📈 Your dashboard will now show:")
    print("   ✅ Latest 2026 market data")
    print("   ✅ Current NIFTY 50 prices")
    print("   ✅ Today's date (2026-09-21)")
    print("\n🚀 Restart your frontend to see fresh data!")
    print("   http://localhost:5173\n")

if __name__ == "__main__":
    asyncio.run(update_market_data())
