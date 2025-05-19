import os
from dotenv import load_dotenv
import asyncio
import json
from typing import Dict, Optional
import re
from httpx import AsyncClient
import random
from app.utils import (
    create_http_client,
    make_request_with_retry,
    build_city_code_params,
    extract_scripts_from_page,
    parse_median_prices,
    filter_last_3_years,
)

load_dotenv()

city_url = os.getenv("CITY_URL")
median_price_url = os.getenv("MEDIAN_PRICE_URL")

async def get_city_code(client: AsyncClient, state: str, city: str) -> Optional[str]:
    """
    Fetches the city code from Redfin's autocomplete API.
    """
    await asyncio.sleep(random.uniform(1, 3))
    
    location = f"{city}, {state}"
    url = city_url.format(city=city, state=state)
    params =  params = build_city_code_params(location)

    try:
        response = await make_request_with_retry(client, 'get', url, params=params)
        if not response:
            return None
            
        clean_response = response.text.replace("{}&&", "")
        data = json.loads(clean_response)

        for entity in data.get("payload", {}).get("sections", [{}])[0].get("rows", []):
            if str(entity.get("type")) == "2":
                url_path = entity.get("url", "")
                match = re.search(r'/city/(\d+)/', url_path)
                if match:
                    return match.group(1)
        return None
    except Exception as e:
        print(f"Error getting city code: {e}")
        return None


async def get_median_sale_prices_data(state: str, city: str) -> Optional[Dict[str, int]]:
    """
    Fetches the city code from Redfin's autocomplete API.
    """
    try:
        client = await create_http_client()

        try:
            city_code = await get_city_code(client, state, city)
            if not city_code:
                print(f"Could not find city code for {city}, {state}")
                return None

            await asyncio.sleep(random.uniform(2, 5))

            url = median_price_url.format(city_code=city_code, state=state, city=city)
            response = await make_request_with_retry(client, 'get', url)
            if not response:
                print(f"Failed to get data for {city}, {state}")
                return None

            scripts = extract_scripts_from_page(response.text)
            median_prices = parse_median_prices(scripts)

            if not median_prices:
                print(f"No median price data found for {city}, {state}")
                return None

            return filter_last_3_years(median_prices)

        except Exception as e:
            print(f"Unexpected error in get_median_sale_prices_data: {e}")
            import traceback
            traceback.print_exc()
            return None

        finally:
            await client.aclose()

    except Exception as e:
        print(f"Error creating HTTP client: {e}")
        return None
