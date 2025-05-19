import os
import pytest
import importlib
import sys
from unittest.mock import patch, AsyncMock, MagicMock
from contextlib import AsyncExitStack
from fastapi import FastAPI
from app.main import lifespan, app
import runpy

@pytest.mark.asyncio
async def test_lifespan_startup_shutdown():
    # Create a mock FastAPI app
    mock_app = MagicMock(spec=FastAPI)
    mock_app.state = MagicMock()
    
    # Mock the database functions
    mock_client = MagicMock()
    mock_collection = MagicMock()
    
    # Use AsyncExitStack for managing the context
    async with AsyncExitStack() as stack:
        # Mock connect_to_mongo
        connect_mock = AsyncMock(return_value=(mock_client, mock_collection))
        stack.enter_context(patch('app.main.connect_to_mongo', connect_mock))
        
        # Mock close_mongo_connection
        close_mock = AsyncMock()
        stack.enter_context(patch('app.main.close_mongo_connection', close_mock))
        
        # Execute the lifespan context manager
        lifespan_gen = lifespan(mock_app)
        await lifespan_gen.__aenter__()
        
        # Check that connect was called and state was set correctly
        connect_mock.assert_called_once()
        assert mock_app.state.mongo_client == mock_client
        assert mock_app.state.mongo_collection == mock_collection
        
        # Now trigger the exit
        await lifespan_gen.__aexit__(None, None, None)
        
        # Check that close was called with the right client
        close_mock.assert_called_once_with(mock_client)


def test_app_initialization():
    os.environ["API_TITLE"] = "Redfin Median Price API Test"
    os.environ["API_VERSION"] = "0.1.0-test"
    
    import app.main
    importlib.reload(app.main)
    
    # After reload, get the FastAPI app instance from the module
    fastapi_app = app.main.app
    
    expected_title = os.getenv("API_TITLE")
    expected_version = os.getenv("API_VERSION")
    
    assert fastapi_app.title == expected_title
    assert fastapi_app.version == expected_version
    assert fastapi_app.router.lifespan_context == app.main.lifespan
    assert len(fastapi_app.routes) > 0


@pytest.mark.asyncio
async def test_main_module_execution():
    with patch('uvicorn.run') as mock_run:
        # run the module as __main__
        runpy.run_module('app.main', run_name="__main__")
        
        mock_run.assert_called_once()
        args, kwargs = mock_run.call_args
        assert "main:app" in args[0]
        assert kwargs.get("host") == "0.0.0.0"
        assert kwargs.get("port") == 8000