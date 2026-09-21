"""
Test rate limiting middleware
"""
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.rate_limit import RateLimitMiddleware


@pytest.fixture
def rate_limited_app():
    app = FastAPI()
    app.add_middleware(RateLimitMiddleware, calls=5, period=60)
    
    @app.get("/test")
    def test_endpoint():
        return {"message": "success"}
    
    return app


def test_rate_limit_allows_requests_under_limit(rate_limited_app):
    """Test that requests under the limit are allowed"""
    client = TestClient(rate_limited_app)
    
    for _ in range(5):
        response = client.get("/test")
        assert response.status_code == 200
        assert response.json() == {"message": "success"}


def test_rate_limit_blocks_requests_over_limit(rate_limited_app):
    """Test that requests over the limit are blocked"""
    client = TestClient(rate_limited_app)
    
    # Make 5 successful requests
    for _ in range(5):
        response = client.get("/test")
        assert response.status_code == 200
    
    # 6th request should be rate limited
    response = client.get("/test")
    assert response.status_code == 429
    assert "Rate limit exceeded" in response.json()["detail"]


def test_rate_limit_headers(rate_limited_app):
    """Test that rate limit headers are present"""
    client = TestClient(rate_limited_app)
    
    response = client.get("/test")
    assert response.status_code == 200
    assert "X-RateLimit-Limit" in response.headers
    assert "X-RateLimit-Remaining" in response.headers
    assert "X-RateLimit-Reset" in response.headers
    assert response.headers["X-RateLimit-Limit"] == "5"
