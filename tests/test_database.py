import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorCollection

from app.database import connect_to_mongo, close_mongo_connection


@pytest.mark.asyncio
async def test_connect_to_mongo_success():
    # Create mock client and collection
    mock_client = MagicMock(spec=AsyncIOMotorClient)
    mock_collection = MagicMock(spec=AsyncIOMotorCollection)
    
    # Mock the AsyncIOMotorClient constructor
    with patch('app.database.AsyncIOMotorClient', return_value=mock_client):
        # Mock accessing the database and collection
        mock_client.__getitem__.return_value.__getitem__.return_value = mock_collection
        
        # Mock the create_index method
        mock_collection.create_index = AsyncMock()
        
        # Call the function
        client, collection = await connect_to_mongo()
        
        # Check that we got the right return values
        assert client == mock_client
        assert collection == mock_collection
        
        # Verify create_index was called
        mock_collection.create_index.assert_called_once()


@pytest.mark.asyncio
async def test_connect_to_mongo_failure():
    # Mock AsyncIOMotorClient to raise an exception
    with patch('app.database.AsyncIOMotorClient', side_effect=Exception("Connection error")):
        # Call the function
        client, collection = await connect_to_mongo()
        
        # Check that we got None for both return values
        assert client is None
        assert collection is None


@pytest.mark.asyncio
async def test_close_mongo_connection():
    # Create mock client
    mock_client = MagicMock(spec=AsyncIOMotorClient)
    
    # Call the function
    await close_mongo_connection(mock_client)
    
    # Verify close was called
    mock_client.close.assert_called_once()