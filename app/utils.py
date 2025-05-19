import asyncio
from datetime import datetime, timedelta
import re
from httpx import AsyncClient, Response
from typing import Dict, List, Optional
from urllib.parse import quote
import uuid
import random
import string

from parsel import Selector


def generate_timestamps():
    """
    Generate and return current, previous (yesterday), and next (tomorrow) datetime objects.
    """
    now = datetime.now()
    yesterday = now - timedelta(days=1)
    tomorrow = now + timedelta(days=1)

    return now, yesterday, tomorrow


def generate_iso_formats(now: datetime) -> str:
    """
    Generate an ISO 8601 formatted timestamp string from a datetime object 
    and URL-encode it.
    """
    iso_now = now.strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
    return quote(iso_now)


def generate_unix_timestamps(now: datetime, yesterday: datetime, tomorrow: datetime):
    """
    Convert datetime objects to Unix timestamps in milliseconds.
    """
    return (
        int(now.timestamp() * 1000),
        int(yesterday.timestamp() * 1000),
        int(tomorrow.timestamp() * 1000),
    )


def generate_misc_ids(unix_now_ms: int) -> dict:
    """
    Generate a dictionary of various randomized ID values and formatted strings
    used for constructing dynamic cookies.
    """
    return {
        "browser_id": ''.join(random.choices(string.ascii_letters + string.digits, k=24)),
        "consent_id": str(uuid.uuid4()),
        "gcl_au": f"1.1.{random.randint(1_000_000_000, 9_999_999_999)}.{unix_now_ms}",
        "pdst_id": ''.join(random.choices('0123456789abcdef', k=32)),
        "scor_uid": ''.join(random.choices('0123456789abcdef', k=32)),
        "gid_value": f"GA1.2.{random.randint(1_000_000_000, 9_999_999_999)}.{unix_now_ms}",
        "tt_value": ''.join(random.choices('0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ', k=24)),
        "ga_value": f"GA1.2.{random.randint(1_000_000_000, 9_999_999_999)}.{unix_now_ms}",
        "uetsid":  f"{''.join(random.choices('0123456789abcdef', k=32))}|"
                f"{random.choice('0123456789abcdefghijklmnopqrstuvwxyz')}|2|fvw|0|1959",
        "uetvid": f"{''.join(random.choices('0123456789abcdef', k=32))}|"
                f"{random.choice('0123456789abcdefghijklmnopqrstuvwxyz')}|{unix_now_ms}|1|1|bat.bing.com/p/conversions/c/a",
        "ttcsid_id": ''.join(random.choices('0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ', k=20)),
        "waf_token": f"{uuid.uuid4()}:BQoAqBA15hAsAAAA:{generate_random_hash(80)}",
    }


def format_cookie_parts(
    now: datetime,
    iso_encoded: str,
    unix_now: int,
    unix_yesterday: int,
    unix_tomorrow: int,
    ids: dict
    ) -> list:
    """
    Format a list of simulated cookie strings using the provided timestamps and ID values.
    """
    
    formatted_date = now.strftime('%a+%b+%d+%Y+%H%%3A%M%%3A%S+GMT%2B0500+(Pakistan+Standard+Time)')
    return [
        f"RF_BROWSER_ID={ids['browser_id']}",
        f"RF_BROWSER_ID_GREAT_FIRST_VISIT_TIMESTAMP={iso_encoded}",
        "RF_BID_UPDATED=1",
        f"_gcl_au={ids['gcl_au']}",
        f"__pdst={ids['pdst_id']}",
        f"_scor_uid={ids['scor_uid']}",
        f"_gid={ids['gid_value']}",
        "_tt_enable_cookie=1",
        f"_ttp=01{ids['tt_value']}.tt.1",
        f"_ga_1GT3SM32XK=GS2.2.s{unix_now}$o1$g0$t{unix_now}$j0$l0$h0",
        "RF_VISITED=true",
        "RF_TRAFFIC_SEGMENT=non-organic",
        f"OptanonAlertBoxClosed={now.strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3]}Z",
        f"_ga_928P0PZ00X=GS2.1.s{unix_now}$o3$g1$t{unix_now}$j60$l0$h0",
        (
            "OptanonConsent=isGpcEnabled=0&datestamp=" + formatted_date +
            f"&version=202403.1.0&browserGpcFlag=0&isIABGlobal=false&hosts="
            f"&consentId={ids['consent_id']}&interactionCount=1&isAnonUser=1"
            "&landingPath=NotLandingPage&groups=C0001%3A1%2CC0003%3A1%2CSPD_BG%3A1%2CC0002%3A1%2CC0004%3A1"
            "&AwaitingReconsent=false&geolocation=PK%3BPB"
        ),
        f"ttcsid={unix_now}::tyWJJqomUsH2soBhoHjl.2.{unix_now}",
        "AMP_TOKEN=%24NOT_FOUND",
        f"_ga={ids['ga_value']}",
        "RF_LAST_NAV=1",
        "audS=t",
        "FEED_COUNT=%5B%22%22%2C%22f%22%5D",
        f"ki_t={unix_now}%3B{unix_yesterday}%3B{unix_now}%3B1%3B2",
        "ki_r=aHR0cHM6Ly9jaGF0Z3B0LmNvbS8%3D",
        "RF_CORVAIR_LAST_VERSION=576.0.0",
        f"_uetsid={ids['uetsid']}",
        f"_uetvid={ids['uetvid']}",
        "RF_BROWSER_CAPABILITIES=%7B%22screen-size%22%3A3%2C%22events-touch%22%3Afalse%2C%22ios-app-store%22%3Afalse%2C%22google-play-store%22%3Afalse%2C%22ios-web-view%22%3Afalse%2C%22android-web-view%22%3Afalse%7D",
        f"ttcsid_{ids['ttcsid_id']}={unix_now}::p8--6PEFPNRDcxtDFjmf.2.{unix_now + 17000}",
        f"aws-waf-token={ids['waf_token']}",
        f"_dd_s=rum=0&expire={unix_tomorrow}",
    ]


def generate_dynamic_cookie() -> str:
    """
    Generate a dynamic cookie string.
    """
    now, yesterday, tomorrow = generate_timestamps()
    encoded_iso_now = generate_iso_formats(now)
    unix_now, unix_yesterday, unix_tomorrow = generate_unix_timestamps(now, yesterday, tomorrow)
    ids = generate_misc_ids(unix_now)
    parts = format_cookie_parts(now, encoded_iso_now, unix_now, unix_yesterday, unix_tomorrow, ids)
    return "; ".join(parts)

def generate_random_hash(length=32):
    """Generate a random string that looks like a hash/token value"""
    chars = string.ascii_letters + string.digits + '+/='
    return ''.join(random.choice(chars) for _ in range(length))


USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/97.0.4692.71 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.2 Safari/605.1.15",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36",
]


def get_random_user_agent() -> str:
    """
    Select and return a random User-Agent string from a predefined list.
    """
    return random.choice(USER_AGENTS)


async def create_http_client() -> AsyncClient:
    """
    Create and return an instance of httpx.AsyncClient with custom headers and settings.
    """
    return AsyncClient(
        headers={
            "User-Agent": get_random_user_agent(),
            "Accept": "*/*",
            "Referer": "https://www.redfin.com/",
            "Accept-Language": "en-GB,en-US;q=0.9,en;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
            "Cookie": generate_dynamic_cookie()
        },
        follow_redirects=True,
        http2=True,
        timeout=30,
    )


async def make_request_with_retry(client: AsyncClient, method: str, url: str, **kwargs) -> Optional[Response]:
    """
    Make an HTTP request with retry functionality
    """
    MAX_RETRIES = 3
    retry_count = 0
    
    while retry_count < MAX_RETRIES:
        try:
            if method.lower() == 'get':
                response = await client.get(url, **kwargs)
            elif method.lower() == 'post':
                response = await client.post(url, **kwargs)
            else:
                print(f"Unsupported HTTP method: {method}")
                return None
                
            if response.status_code in [200, 201, 202]:
                return response
                
            print(f"Request failed with status {response.status_code}, attempt {retry_count + 1}/{MAX_RETRIES}")
            
        except Exception as e:
            print(f"Request error on attempt {retry_count + 1}/{MAX_RETRIES}: {e}")
        
        retry_count += 1
        if retry_count < MAX_RETRIES:
            # Exponential backoff with jitter
            wait_time = (2 ** retry_count) + random.uniform(0, 1)
            print(f"Waiting {wait_time:.2f} seconds before retrying...")
            await asyncio.sleep(wait_time)
    
    print(f"All {MAX_RETRIES} retry attempts failed")
    return None


def build_city_code_params(location: str) -> dict:
    """
    Build the query parameters for the city code API request.
    """
    return {
        "location": location,
        "start": "0",
        "count": "10",
        "v": "2",
        "al": "1",
        "iss": "false",
        "ooa": "true",
        "mrs": "false",
        "region_id": "NaN",
        "region_type": "NaN",
        "lat": "",
        "lng": "",
        "includeAddressInfo": "false"
    }
    

def extract_scripts_from_page(html: str) -> List[str]:
    """
    Extract all script contents from an HTML page that contain the specific substring "_tLAB.wait(function()".
    """
    selector = Selector(html)
    return selector.xpath('//script[contains(text(), "_tLAB.wait(function()")]/text()').getall()


def parse_median_prices(scripts: List[str]) -> Dict[str, int]:
    """
    Parse median sale prices by extracting and decoding JSON-like data embedded within script strings.
    """
    median_prices = {}
    median_sale_pattern = r'\[\{\\\"label\\\":\\\"Median Sale Price\\\".*?\\\"aggregateData\\\":\[(.*?)\]'

    for script in scripts:
        median_match = re.search(median_sale_pattern, script)
        if median_match:
            try:
                aggregate_data_str = median_match.group(1)
                clean_data_str = aggregate_data_str.replace('\\\\', '\\').replace('\\"', '"')
                data_objects = re.finditer(r'\{.*?"date":"(.*?)".*?"value":"(.*?)".*?\}', clean_data_str)

                for match in data_objects:
                    date = match.group(1)
                    value = match.group(2).replace(',', '')
                    date_str = datetime.strptime(date, '%Y-%m-%d').strftime('%Y-%m')
                    if '.' in value:
                        value = value.split('.')[0]
                    median_prices[date_str] = int(value)

                if median_prices:
                    break
            except Exception as e:
                print(f"Error processing aggregateData: {e}")
    return median_prices


def filter_last_3_years(data: Dict[str, int]) -> Dict[str, int]:
    """
    Filter a dictionary of date-string keys to keep only entries from the last 3 years.
    """
    threshold = datetime(datetime.now().year - 3, datetime.now().month, 1)
    return {k: v for k, v in data.items() if datetime.strptime(k, "%Y-%m") >= threshold}