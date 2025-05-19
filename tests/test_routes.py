import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from fastapi.testclient import TestClient
from fastapi import FastAPI

from app.routes import router
from app.models import APIInfo


@pytest.fixture
def test_app():
    app = FastAPI()
    app.include_router(router)
    
    # Add state to simulate the MongoDB connection
    app.state.mongo_client = MagicMock()
    app.state.mongo_collection = AsyncMock()
    
    return app


@pytest.fixture
def client(test_app):
    return TestClient(test_app)


def test_root_endpoint(client):
    response = client.get("/")
    
    assert response.status_code == 200
    
    data = response.json()
    assert isinstance(data, dict)
    assert "name" in data
    assert "description" in data
    assert "endpoints" in data
    
    # Verify the response matches the APIInfo model
    api_info = APIInfo(**data)
    assert api_info.name == "Redfin Median Price API"
    assert "/median-prices" in api_info.endpoints


@pytest.mark.asyncio
async def test_get_median_prices_cached_data(test_app, client):
    # Mock the get_fresh_cached_data function to return cached data
    test_prices = {"2023-01": 500000, "2023-02": 510000}
    
    with patch('app.routes.get_fresh_cached_data', 
               new_callable=AsyncMock, return_value=test_prices):
        # We don't need to mock fetch_and_cache_prices since it shouldn't be called
        
        response = client.get("/median-prices?state=TX&city=Austin")
        
        assert response.status_code == 200
        assert response.json() == test_prices


@pytest.mark.asyncio
async def test_get_median_prices_fetch_new_data(test_app, client):
    # Mock get_fresh_cached_data to return None (no cached data)
    with patch('app.routes.get_fresh_cached_data', 
               new_callable=AsyncMock, return_value=None):
        # Mock fetch_and_cache_prices to return new data
        test_prices = {"2023-01": 500000, "2023-02": 510000}
        with patch('app.routes.fetch_and_cache_prices', 
                   new_callable=AsyncMock, return_value=test_prices):
            
            response = client.get("/median-prices?state=TX&city=Austin")
            
            assert response.status_code == 200
            assert response.json() == test_prices


def test_get_median_prices_validation(client):
    # Test with missing state parameter
    response = client.get("/median-prices?city=Austin")
    assert response.status_code == 422  # Validation error
    
    # Test with missing city parameter
    response = client.get("/median-prices?state=TX")
    assert response.status_code == 422  # Validation error
    
    # Test with invalid state (too long)
    response = client.get("/median-prices?state=Texas&city=Austin")
    assert response.status_code == 422 