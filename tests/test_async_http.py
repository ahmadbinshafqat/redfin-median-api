import pytest
import asyncio
from unittest.mock import patch, AsyncMock, MagicMock
import httpx
import random

from app.utils import (
    create_http_client,
    make_request_with_retry,
    generate_random_hash
)


@pytest.mark.asyncio
async def test_create_http_client():
    with patch('app.utils.get_random_user_agent', return_value="Mozilla/5.0 Test Agent"):
        with patch('app.utils.generate_dynamic_cookie', return_value="test_cookie=value"):
            client = await create_http_client()
            
            # Check client configuration
            assert isinstance(client, httpx.AsyncClient)
            assert client.headers["User-Agent"] == "Mozilla/5.0 Test Agent"
            assert client.headers["Cookie"] == "test_cookie=value"
            assert client.headers["Referer"] == "https://www.redfin.com/"
            assert client.follow_redirects is True
            
            # Close the client to prevent resource warning
            await client.aclose()


@pytest.mark.asyncio
async def test_make_request_with_retry_success_first_attempt():
    # Create mock client and response
    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_response = MagicMock(spec=httpx.Response)
    mock_response.status_code = 200
    
    # Set up the mock client to return our mock response for GET
    mock_client.get = AsyncMock(return_value=mock_response)
    
    # Call the function
    result = await make_request_with_retry(mock_client, 'get', 'https://test.com')
    
    # Check we got the expected response
    assert result == mock_response
    
    # Verify client.get was called once with the correct URL
    mock_client.get.assert_called_once_with('https://test.com')


@pytest.mark.asyncio
async def test_make_request_with_retry_success_after_retry():
    # Create mock client and responses
    mock_client = AsyncMock(spec=httpx.AsyncClient)
    
    # First attempt fails with 500
    fail_response = MagicMock(spec=httpx.Response)
    fail_response.status_code = 500
    
    # Second attempt succeeds with 200
    success_response = MagicMock(spec=httpx.Response)
    success_response.status_code = 200
    
    # Set up the mock client to return fail then success
    mock_client.post = AsyncMock(side_effect=[fail_response, success_response])
    
    # Mock sleep to avoid waiting during test
    with patch('asyncio.sleep', new_callable=AsyncMock):
        # Call the function
        result = await make_request_with_retry(mock_client, 'post', 'https://test.com', data={"key": "value"})
        
        # Check we got the expected response
        assert result == success_response
        
        # Verify client.post was called twice with the correct URL and data
        assert mock_client.post.call_count == 2
        mock_client.post.assert_called_with('https://test.com', data={"key": "value"})


@pytest.mark.asyncio
async def test_make_request_with_retry_all_attempts_fail():
    # Create mock client
    mock_client = AsyncMock(spec=httpx.AsyncClient)
    
    # Set up the mock client to raise an exception each time
    mock_client.get = AsyncMock(side_effect=httpx.RequestError("Connection error"))
    
    # Mock sleep to avoid waiting during test
    with patch('asyncio.sleep', new_callable=AsyncMock):
        # Call the function
        result = await make_request_with_retry(mock_client, 'get', 'https://test.com')
        
        # Check we got None as all attempts failed
        assert result is None
        
        # Verify client.get was called 3 times (default MAX_RETRIES)
        assert mock_client.get.call_count == 3


@pytest.mark.asyncio
async def test_make_request_with_retry_unsupported_method():
    # Create mock client
    mock_client = AsyncMock(spec=httpx.AsyncClient)
    
    # Call with unsupported method
    result = await make_request_with_retry(mock_client, 'put', 'https://test.com')
    
    # Check we got None for unsupported method
    assert result is None
    
    # Verify neither get nor post were called
    mock_client.get.assert_not_called()
    mock_client.post.assert_not_called()


def test_generate_random_hash_default_length():
    hash_value = generate_random_hash()
    
    # Check length is the default (32)
    assert len(hash_value) == 32
    
    # Check it contains only valid characters
    valid_chars = set('0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ+/=')
    assert all(c in valid_chars for c in hash_value)


def test_generate_random_hash_custom_length():
    hash_value = generate_random_hash(length=64)
    
    # Check length is as specified
    assert len(hash_value) == 64
    
    # Generate multiple hashes and verify they're different
    hash1 = generate_random_hash(length=16)
    hash2 = generate_random_hash(length=16)
    
    assert hash1 != hash2  # This could theoretically fail but is extremely unlikely


def test_generate_random_hash_randomness():
    # Set the seed to ensure repeatable test
    random.seed(42)
    hash1 = generate_random_hash(length=20)
    
    # Reset seed to same value
    random.seed(42)
    hash2 = generate_random_hash(length=20)
    
    # With the same seed, we should get the same sequence
    assert hash1 == hash2
    
    # Now let's confirm it produces different values with different seeds
    random.seed(100)
    hash3 = generate_random_hash(length=20)
    assert hash1 != hash3