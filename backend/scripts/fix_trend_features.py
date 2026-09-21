"""
Fix all missing Google Trends features for the 2026 dataset
"""
import asyncio
from datetime import date

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.ext.asyncio import async_sessionmaker

from app.core.config import get_settings
from app.services.feature_engineering_service import FeatureEngineer
from app.repositories.search_term_repo import SearchTermRepository


async def fix_trend_features():
    """Add missing Google Trends features for all dates"""
    settings = get_settings()
    
    engine = create_async_engine(settings.database_url.replace("postgresql://", "postgresql+asyncpg://"))
    async_session_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session_maker() as session:
        feature_service = FeatureEngineer(session)
        term_repo = SearchTermRepository(session)
        
        # Get all active search terms
        terms = await term_repo.get_all(active_only=True)
        term_ids = [t.id for t in terms]
        
        print("=" * 70)
        print("FIXING GOOGLE TRENDS FEATURES")
        print("=" * 70)
        print(f"\nSearch terms found: {[t.term for t in terms]}")
        
        # Generate features for the full date range
        print("\nGenerating features for 2024-01-01 to 2026-09-21...")
        
        try:
            result = await feature_service.generate_features(
                symbol="^NSEI",
                search_term_ids=term_ids,
                start_date=date(2024, 1, 1),
                end_date=date(2026, 9, 21),
                persist=True
            )
            
            print(f"\nSuccess! Generated {result.get('total_features', 0)} features")
            print(f"   Feature names: {result.get('feature_count', 0)} unique features")
            
        except Exception as e:
            print(f"\nError: {e}")
            import traceback
            traceback.print_exc()
    
    await engine.dispose()
    
    print("\n" + "=" * 70)
    print("FEATURE FIX COMPLETE!")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(fix_trend_features())