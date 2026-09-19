import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_search_term(client: AsyncClient):
    response = await client.post("/api/search-terms/", json={"term": "recession", "category": "macro"})
    assert response.status_code == 201
    data = response.json()
    assert data["term"] == "recession"
    assert data["category"] == "macro"
    assert "id" in data


@pytest.mark.asyncio
async def test_create_duplicate_search_term(client: AsyncClient):
    await client.post("/api/search-terms/", json={"term": "recession", "category": "macro"})
    response = await client.post("/api/search-terms/", json={"term": "recession", "category": "macro"})
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_get_search_term(client: AsyncClient):
    create_response = await client.post("/api/search-terms/", json={"term": "inflation", "category": "macro"})
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
    await client.post("/api/search-terms/", json={"term": "term1", "category": "cat1"})
    await client.post("/api/search-terms/", json={"term": "term2", "category": "cat2"})
    response = await client.get("/api/search-terms/")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2


@pytest.mark.asyncio
async def test_update_search_term(client: AsyncClient):
    create_response = await client.post("/api/search-terms/", json={"term": "old_name", "category": "cat"})
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
    create_response = await client.post("/api/search-terms/", json={"term": "to_delete", "category": "cat"})
    term_id = create_response.json()["id"]
    response = await client.delete(f"/api/search-terms/{term_id}")
    assert response.status_code == 200
    get_response = await client.get(f"/api/search-terms/{term_id}")
    assert get_response.status_code == 404


@pytest.mark.asyncio
async def test_validation_empty_term(client: AsyncClient):
    response = await client.post("/api/search-terms/", json={"term": "  ", "category": "cat"})
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_validation_short_term(client: AsyncClient):
    response = await client.post("/api/search-terms/", json={"term": "a", "category": "cat"})
    assert response.status_code == 422
