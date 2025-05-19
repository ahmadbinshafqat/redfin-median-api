import pytest
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock, AsyncMock

from app.services import (
    standardize_location,
    is_cache_fresh, 
    get_fresh_cached_data,
    fetch_and_cache_prices
)
from fastapi import HTTPException


def test_standardize_location():
    # Test various inputs
    assert standardize_location("tx", "austin") == ("TX", "Austin")
    assert standardize_location("TX", "AUSTIN") == ("TX", "Austin")
    assert standardize_location("tX", "Austin") == ("TX", "Austin")
    assert standardize_location("NY", "new york") == ("NY", "New York")
    assert standardize_location("ca", "san francisco") == ("CA", "San Francisco")


def test_is_cache_fresh():
    # Test with fresh data (1 day old)
    yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    assert is_cache_fresh(yesterday) is True
    
    # Test with stale data (10 days old)
    old_date = (datetime.now() - timedelta(days=10)).strftime("%Y-%m-%d")
    assert is_cache_fresh(old_date) is False
    
    # Test with custom max_age
    three_days_ago = (datetime.now() - timedelta(days=3)).strftime("%Y-%m-%d")
    assert is_cache_fresh(three_days_ago, max_age_days=2) is False
    assert is_cache_fresh(three_days_ago, max_age_days=5) is True


@pytest.mark.asyncio
async def test_get_fresh_cached_data_with_fresh_data():
    # Mock collection
    collection = AsyncMock()
    fresh_date = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    test_data = {"state": "TX", "city": "Austin", "last_updated": fresh_date, "data": {"2023-01": 500000}}
    
    # Set up the mock to return our test data
    collection.find_one = AsyncMock(return_value=test_data)
    
    result = await get_fresh_cached_data(collection, "TX", "Austin")
    
    # Check result matches our test data
    assert result == test_data["data"]
    # Verify the collection was queried with correct params
    collection.find_one.assert_called_once_with({"state": "TX", "city": "Austin"})


@pytest.mark.asyncio
async def test_get_fresh_cached_data_with_stale_data():
    # Mock collection
    collection = AsyncMock()
    stale_date = (datetime.now() - timedelta(days=10)).strftime("%Y-%m-%d")
    test_data = {"state": "TX", "city": "Austin", "last_updated": stale_date, "data": {"2023-01": 500000}}
    
    # Set up the mock to return our test data
    collection.find_one = AsyncMock(return_value=test_data)
    
    result = await get_fresh_cached_data(collection, "TX", "Austin")
    
    # Check result is None since data is stale
    assert result is None
    # Verify the collection was queried with correct params
    collection.find_one.assert_called_once_with({"state": "TX", "city": "Austin"})


@pytest.mark.asyncio
async def test_get_fresh_cached_data_with_no_data():
    # Mock collection
    collection = AsyncMock()
    
    # Set up the mock to return None (no data found)
    collection.find_one = AsyncMock(return_value=None)
    
    result = await get_fresh_cached_data(collection, "TX", "Austin")
    
    # Check result is None since no data found
    assert result is None
    # Verify the collection was queried with correct params
    collection.find_one.assert_called_once_with({"state": "TX", "city": "Austin"})


@pytest.mark.asyncio
async def test_fetch_and_cache_prices_success():
    collection = AsyncMock()
    
    test_prices = {"2023-01": 500000}
    
    # Mock the external fetch function
    with patch('app.services.get_median_sale_prices_data', 
               new_callable=AsyncMock, return_value=test_prices):
        # Mock the update function
        with patch('app.services.update_city_data', new_callable=AsyncMock) as mock_update:
            result = await fetch_and_cache_prices(collection, "TX", "Austin")
            
            # Check result matches our test prices
            assert result == test_prices
            
            # Verify update was called with correct params
            mock_update.assert_called_once_with(collection, "TX", "Austin", test_prices)


@pytest.mark.asyncio
async def test_fetch_and_cache_prices_no_fresh_data_but_cached():
    collection = AsyncMock()
    
    # No fresh data from API
    with patch('app.services.get_median_sale_prices_data', 
               new_callable=AsyncMock, return_value=None):
        # But we have cached data
        cached_data = {
            "state": "TX", 
            "city": "Austin", 
            "last_updated": "2023-01-01", 
            "data": {"2023-01": 500000}
        }
        collection.find_one = AsyncMock(return_value=cached_data)
        
        result = await fetch_and_cache_prices(collection, "TX", "Austin")
        
        # Check result matches our cached data
        assert result == cached_data["data"]


@pytest.mark.asyncio
async def test_fetch_and_cache_prices_no_data_at_all():
    collection = AsyncMock()
    
    # No fresh data from API
    with patch('app.services.get_median_sale_prices_data', 
               new_callable=AsyncMock, return_value=None):
        # And no cached data
        collection.find_one = AsyncMock(return_value=None)
        
        # Should raise HTTPException
        with pytest.raises(HTTPException) as excinfo:
            await fetch_and_cache_prices(collection, "TX", "Austin")
        
        # Check exception details
        assert excinfo.value.status_code == 404
        assert "Could not find data for Austin, TX" in str(excinfo.value.detail)