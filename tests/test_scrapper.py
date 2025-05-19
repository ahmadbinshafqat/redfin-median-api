import pytest
from unittest.mock import patch, AsyncMock, MagicMock
import json
from httpx import Response

from app.redfin_median_prices_scraper import (
    get_city_code,
    get_median_sale_prices_data
)


@pytest.mark.asyncio
async def test_get_city_code_success():
    # Create a mock client
    mock_client = AsyncMock()
    
    # Mock response from Redfin
    mock_response = MagicMock()
    mock_response.text = '{}&&{"payload":{"sections":[{"rows":[{"type":"2","url":"/ca/los-angeles/city/12345/"}]}]}}'
    
    # Mock the make_request_with_retry function
    with patch('app.redfin_median_prices_scraper.make_request_with_retry', 
               new_callable=AsyncMock, return_value=mock_response):
        
        city_code = await get_city_code(mock_client, "CA", "Los Angeles")
        
        # Check we got the expected city code
        assert city_code == "12345"


@pytest.mark.asyncio
async def test_get_city_code_no_match():
    # Create a mock client
    mock_client = AsyncMock()
    
    # Mock response with no matching city data
    mock_response = MagicMock()
    mock_response.text = '{}&&{"payload":{"sections":[{"rows":[]}]}}'
    
    # Mock the make_request_with_retry function
    with patch('app.redfin_median_prices_scraper.make_request_with_retry', 
               new_callable=AsyncMock, return_value=mock_response):
        
        city_code = await get_city_code(mock_client, "XX", "Nonexistent")
        
        # Check we got None as there's no matching city
        assert city_code is None


@pytest.mark.asyncio
async def test_get_city_code_request_failure():
    # Create a mock client
    mock_client = AsyncMock()
    
    # Mock make_request_with_retry to return None (request failure)
    with patch('app.redfin_median_prices_scraper.make_request_with_retry', 
               new_callable=AsyncMock, return_value=None):
        
        city_code = await get_city_code(mock_client, "CA", "Los Angeles")
        
        # Check we got None as the request failed
        assert city_code is None


@pytest.mark.asyncio
async def test_get_median_sale_prices_data_no_city_code():
    # Mock HTTP client creation
    mock_client = AsyncMock()
    
    with patch('app.redfin_median_prices_scraper.create_http_client', 
               new_callable=AsyncMock, return_value=mock_client):
        
        # Mock get_city_code to return None (city not found)
        with patch('app.redfin_median_prices_scraper.get_city_code', 
                   new_callable=AsyncMock, return_value=None):
            
            prices = await get_median_sale_prices_data("XX", "Nonexistent")
            
            # Check we got None as no city code was found
            assert prices is None


@pytest.mark.asyncio
async def test_get_median_sale_prices_data_request_failure():
    # Mock HTTP client creation
    mock_client = AsyncMock()
    
    with patch('app.redfin_median_prices_scraper.create_http_client', 
               new_callable=AsyncMock, return_value=mock_client):
        
        # Mock get_city_code to return a valid code
        with patch('app.redfin_median_prices_scraper.get_city_code', 
                   new_callable=AsyncMock, return_value="12345"):
            
            # Mock make_request_with_retry to return None (request failure)
            with patch('app.redfin_median_prices_scraper.make_request_with_retry', 
                       new_callable=AsyncMock, return_value=None):
                
                prices = await get_median_sale_prices_data("CA", "Los Angeles")
                
                # Check we got None as the request failed
                assert prices is None


@pytest.mark.asyncio
async def test_get_median_sale_prices_data_no_price_data():
    # Mock HTTP client creation
    mock_client = AsyncMock()
    
    with patch('app.redfin_median_prices_scraper.create_http_client', 
               new_callable=AsyncMock, return_value=mock_client):
        
        # Mock get_city_code to return a valid code
        with patch('app.redfin_median_prices_scraper.get_city_code', 
                   new_callable=AsyncMock, return_value="12345"):
            
            # Mock HTML response with no price data
            mock_html = "<html><body>No price data here</body></html>"
            mock_response = MagicMock(spec=Response)
            mock_response.text = mock_html
            
            # Mock the make_request_with_retry function
            with patch('app.redfin_median_prices_scraper.make_request_with_retry', 
                       new_callable=AsyncMock, return_value=mock_response):
                
                # Mock the parse_median_prices function to return empty dict
                with patch('app.redfin_median_prices_scraper.parse_median_prices', 
                           return_value={}):
                    
                    prices = await get_median_sale_prices_data("CA", "Los Angeles")
                    
                    # Check we got None as no price data was found
                    assert prices is None