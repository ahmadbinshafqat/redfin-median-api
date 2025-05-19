from pydantic import BaseModel, Field
from typing import Dict


class APIInfo(BaseModel):
    """Model for API information."""

    name: str = Field(...)
    description: str = Field(...)
    endpoints: Dict[str, str] = Field(...)

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "name": "Redfin Median Price API",
                    "description": "Provides median home prices by city and state.",
                    "endpoints": {"/median-price": "Get median price data."}
                }
            ]
        }
    }
