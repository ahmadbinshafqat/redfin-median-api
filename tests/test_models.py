import pytest
from unittest.mock import patch, MagicMock, AsyncMock
import os

from app.models import APIInfo


def test_api_info_model():
    # Test creating a valid APIInfo object
    api_info = APIInfo(
        name="Test API",
        description="This is a test API",
        endpoints={"/test": "Test endpoint"}
    )
    
    assert api_info.name == "Test API"
    assert api_info.description == "This is a test API"
    assert api_info.endpoints == {"/test": "Test endpoint"}
    
    # Test model validation with dict
    data = {
        "name": "Test API",
        "description": "This is a test API",
        "endpoints": {"/test": "Test endpoint"}
    }
    api_info_from_dict = APIInfo(**data)
    
    assert api_info_from_dict.name == "Test API"
    assert api_info_from_dict.description == "This is a test API"
    assert api_info_from_dict.endpoints == {"/test": "Test endpoint"}


def test_api_info_model_validation():
    # Test with missing required fields
    with pytest.raises(ValueError):
        APIInfo(name="Test API")
    
    with pytest.raises(ValueError):
        APIInfo(name="Test API", description="Description only")
    
    # Test with invalid field types
    with pytest.raises(ValueError):
        APIInfo(
            name="Test API",
            description="This is a test API",
            endpoints="Not a dict"  # Should be a dict
        )


def test_api_info_model_examples():
    # Verify that the model examples are valid
    example = APIInfo.model_config["json_schema_extra"]["examples"][0]
    api_info = APIInfo(**example)
    
    assert api_info.name == "Redfin Median Price API"
    assert "median home prices" in api_info.description.lower()
    assert "/median-price" in api_info.endpoints