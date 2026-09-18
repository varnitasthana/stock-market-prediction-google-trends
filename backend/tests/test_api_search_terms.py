import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base

from app.core.database import Base, get_db
from app.main import app

TEST_DATABASE_URL = "postgresql+asyncpg://postgres:postgres@localhost:5432/stock_prediction_test"


@pytest_asyncio.fixture(scope="function")
async def db_session():
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all, checkfirst=True)
            await conn.run_sync(Base.metadata.create_all)
        async with async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)() as session:
            yield session
    finally:
        await engine.dispose()


@pytest_asyncio.fixture
async def client(db_session: AsyncSession):
    async def override_get_db():
        try:
            yield db_session
            await db_session.commit()
        except Exception:
            await db_session.rollback()
            raise

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test", follow_redirects=True) as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_create_search_term(client: AsyncClient):
    response = await client.post("/api/search-terms", json={"term": "recession", "category": "macro"})
    assert response.status_code == 201
    data = response.json()
    assert data["term"] == "recession"
    assert data["category"] == "macro"
    assert "id" in data


@pytest.mark.asyncio
async def test_create_duplicate_search_term(client: AsyncClient):
    await client.post("/api/search-terms", json={"term": "recession", "category": "macro"})
    response = await client.post("/api/search-terms", json={"term": "recession", "category": "macro"})
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_get_search_term(client: AsyncClient):
    create_response = await client.post("/api/search-terms", json={"term": "inflation", "category": "macro"})
    term_id = create_response.json()["id"]
    response = await client.get(f"/api/search-terms/{term_id}")
    assert response.status_code == 200
    assert response.json()["term"] == "inflation"


@pytest.mark.asyncio
async def test_get_search_term_not_found(client: AsyncClient):
    response = await client.get("/api/search-terms/99999")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_list_search_terms(client: AsyncClient):
    await client.post("/api/search-terms", json={"term": "term1", "category": "cat1"})
    await client.post("/api/search-terms", json={"term": "term2", "category": "cat2"})
    response = await client.get("/api/search-terms")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2


@pytest.mark.asyncio
async def test_update_search_term(client: AsyncClient):
    create_response = await client.post("/api/search-terms", json={"term": "old_name", "category": "cat"})
    term_id = create_response.json()["id"]
    response = await client.put(f"/api/search-terms/{term_id}", json={"term": "new_name", "category": "new_cat"})
    assert response.status_code == 200
    data = response.json()
    assert data["term"] == "new_name"
    assert data["category"] == "new_cat"


@pytest.mark.asyncio
async def test_update_search_term_not_found(client: AsyncClient):
    response = await client.put("/api/search-terms/99999", json={"term": "new_name"})
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_search_term(client: AsyncClient):
    create_response = await client.post("/api/search-terms", json={"term": "to_delete", "category": "cat"})
    term_id = create_response.json()["id"]
    response = await client.delete(f"/api/search-terms/{term_id}")
    assert response.status_code == 200
    get_response = await client.get(f"/api/search-terms/{term_id}")
    assert get_response.status_code == 404


@pytest.mark.asyncio
async def test_validation_empty_term(client: AsyncClient):
    response = await client.post("/api/search-terms", json={"term": "  ", "category": "cat"})
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_validation_short_term(client: AsyncClient):
    response = await client.post("/api/search-terms", json={"term": "a", "category": "cat"})
    assert response.status_code == 422
