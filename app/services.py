from datetime import datetime
from typing import Dict, Optional
from fastapi import HTTPException
from app.redfin_median_prices_scraper import get_median_sale_prices_data


async def get_cached_data(collection, state: str, city: str):
    """Get cached data for a city if it exists."""
    return await collection.find_one({"state": state, "city": city})


async def update_city_data(collection, state: str, city: str, prices: dict):
    """Update or insert data for a city."""
    document = {
        "state": state,
        "city": city,
        "last_updated": datetime.now().strftime("%Y-%m-%d"),
        "data": prices
    }
    await collection.update_one(
        {"state": state, "city": city},
        {"$set": document},
        upsert=True
    )
    

def standardize_location(state: str, city: str) -> tuple[str, str]:
    """
    Standardize location names by formatting the state and city strings.
    """
    return state.upper(), city.title()


def is_cache_fresh(last_updated_str: str, max_age_days: int = 7) -> bool:
    """
    Check if the cached data is still fresh based on the last updated date.
    """
    last_updated = datetime.strptime(last_updated_str, "%Y-%m-%d")
    return (datetime.now() - last_updated).days < max_age_days


async def get_fresh_cached_data(collection, state: str, city: str) -> Optional[Dict[str, float]]:
    """
    Retrieve fresh cached data for the given state and city if available and not stale.
    """
    cached_data = await get_cached_data(collection, state, city)
    if cached_data and "last_updated" in cached_data and is_cache_fresh(cached_data["last_updated"]):
        return cached_data.get("data")
    return None


async def fetch_and_cache_prices(collection,state: str, city: str) -> Dict[str, float]:
    """
    Fetch median sale prices for the specified state and city, update the cache, and return the prices.
    If fresh data cannot be fetched, return cached data if available.
    Raises an HTTPException if no data can be found.
    """
    prices = await get_median_sale_prices_data(state, city)
    if prices:
        await update_city_data(collection, state, city, prices)
        return prices
    cached_data = await get_cached_data(collection, state, city)
    if cached_data and "data" in cached_data:
        return cached_data["data"]
    raise HTTPException(status_code=404, detail=f"Could not find data for {city}, {state}")