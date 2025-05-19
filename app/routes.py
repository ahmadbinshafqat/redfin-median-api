"""
API routes for the Redfin Median Price API.
"""

from fastapi import APIRouter, Query, Request
from typing import Dict

from app.models import APIInfo
from app.services import standardize_location, get_fresh_cached_data, fetch_and_cache_prices

router = APIRouter()


@router.get("/", response_model=APIInfo)
async def root():
    """Root endpoint that returns API information."""
    return {
        "name": "Redfin Median Price API",
        "description": "API to fetch 3-year median sale prices for a city",
        "endpoints": {
            "/median-prices": "GET median prices for a city (parameters: state, city)"
        }
    }


@router.get("/median-prices", response_model=Dict[str, float])
async def get_median_prices(
    request: Request,
    state: str = Query(..., min_length=2, max_length=2, description="State abbreviation (e.g. TX)"),
    city: str = Query(..., min_length=1, description="City name (e.g. Austin)")
    ):
    """
    Endpoint to retrieve median sale prices for a given city and state.
    Returns cached data if fresh; otherwise fetches, caches, and returns new data.
    """
    state, city = standardize_location(state, city)
    collection = request.app.state.mongo_collection

    cached_prices = await get_fresh_cached_data(collection, state, city)
    if cached_prices:
        return cached_prices

    return await fetch_and_cache_prices(collection, state, city)