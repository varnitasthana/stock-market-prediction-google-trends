"""
Full refresh of Google Trends data for all active search terms.
Run this to get the latest fresh Google Trends data from the default start date to today.
"""
import asyncio
import sys
import os
from datetime import date

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.ext.asyncio import async_sessionmaker

from app.core.config import get_settings
from app.pipeline.trends_pipeline import TrendsIngestionService
from app.pipeline.trends_provider import PytrendsProvider
from app.repositories.search_term_repo import SearchTermRepository

settings = get_settings()

async def refresh_trends():
    """Refresh all Google Trends data"""
    print("=" * 70)
    print("🔄 FULL GOOGLE TRENDS REFRESH")
    print("=" * 70)
    
    engine = create_async_engine(
        settings.database_url.replace("postgresql://", "postgresql+asyncpg://")
    )
    async_session_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    try:
        async with async_session_maker() as session:
            term_repo = SearchTermRepository(session)
            terms = await term_repo.get_all(active_only=True)
            
            if not terms:
                print("\n⚠️  No active search terms found!")
                return
            
            print(f"\n📋 Found {len(terms)} active search terms:")
            for t in terms:
                print(f"   • {t.term} (category: {t.category})")
            
            provider = PytrendsProvider()
            trends_service = TrendsIngestionService(session, provider=provider)
            
            end_date = settings.resolved_end_date().isoformat()
            start_date = settings.resolved_start_date().isoformat()
            
            print(f"\n📅 Date range: {start_date} to {end_date}")
            print("\n⏳ Fetching Google Trends data (this may take a while)...")
            
            results = await trends_service.ingest_all_terms(start_date, end_date)
            
            total_inserted = sum(r.get("inserted", 0) for r in results if "error" not in r)
            total_records = sum(r.get("total_records", 0) for r in results if "error" not in r)
            errors = [r for r in results if "error" in r]
            
            print("\n" + "=" * 70)
            print("📊 REFRESH RESULTS")
            print("=" * 70)
            
            for r in results:
                if "error" in r:
                    print(f"   ❌ {r['term']}: {r['error']}")
                else:
                    print(f"   ✅ {r['term']}: {r['inserted']} new / {r['total_records']} total records")
            
            print("\n📈 Summary:")
            print(f"   Total records fetched: {total_records}")
            print(f"   New records inserted: {total_inserted}")
            print(f"   Errors: {len(errors)}")
            
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await engine.dispose()
    
    print("\n" + "=" * 70)
    print("✅ TRENDS REFRESH COMPLETED!")
    print("=" * 70)
    print("\n📈 Your dashboard will now show:")
    print("   ✅ Latest Google Trends data")
    print("   ✅ Fresh interest scores")
    print(f"   ✅ Data up to {date.today()}")
    print("\n🚀 Restart your frontend to see fresh data!")
    print("   http://localhost:5173\n")


if __name__ == "__main__":
    asyncio.run(refresh_trends())