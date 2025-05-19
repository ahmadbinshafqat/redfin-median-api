import pytest
import re
from datetime import datetime
from unittest.mock import patch, MagicMock

from app.utils import (
    generate_timestamps,
    generate_iso_formats,
    generate_unix_timestamps,
    generate_misc_ids,
    format_cookie_parts,
    generate_dynamic_cookie,
    get_random_user_agent,
    build_city_code_params,
    extract_scripts_from_page,
    parse_median_prices,
    filter_last_3_years
)


def test_generate_timestamps():
    now, yesterday, tomorrow = generate_timestamps()
    
    assert isinstance(now, datetime)
    assert isinstance(yesterday, datetime)
    assert isinstance(tomorrow, datetime)
    
    # Test that yesterday is 1 day before now
    assert (now - yesterday).days == 1
    
    # Test that tomorrow is 1 day after now
    assert (tomorrow - now).days == 1


def test_generate_iso_formats():
    test_date = datetime(2023, 1, 1, 12, 0, 0)
    result = generate_iso_formats(test_date)
    
    # Check that result is URL-encoded ISO format
    assert '%3A' in result  # URL-encoded colon
    assert '2023-01-01T' in result
    assert 'Z' in result


def test_generate_unix_timestamps():
    now = datetime(2023, 1, 1, 12, 0, 0)
    yesterday = datetime(2022, 12, 31, 12, 0, 0)
    tomorrow = datetime(2023, 1, 2, 12, 0, 0)
    
    unix_now, unix_yesterday, unix_tomorrow = generate_unix_timestamps(now, yesterday, tomorrow)
    
    # Check that they're integers (milliseconds)
    assert isinstance(unix_now, int)
    assert isinstance(unix_yesterday, int)
    assert isinstance(unix_tomorrow, int)
    
    # Check relative values
    assert unix_yesterday < unix_now < unix_tomorrow
    
    # Check the difference is approximately 1 day in milliseconds
    assert abs((unix_tomorrow - unix_now) - 86400000) < 1000  # Allow small difference due to precision


def test_generate_misc_ids():
    ids = generate_misc_ids(1672574400000)  # Jan 1, 2023 in milliseconds
    
    # Check that all expected keys are present
    expected_keys = [
        'browser_id', 'consent_id', 'gcl_au', 'pdst_id', 'scor_uid',
        'gid_value', 'tt_value', 'ga_value', 'uetsid', 'uetvid',
        'ttcsid_id', 'waf_token'
    ]
    for key in expected_keys:
        assert key in ids
    
    # Check browser_id format (24 alphanumeric chars)
    assert len(ids['browser_id']) == 24
    assert re.match(r'^[a-zA-Z0-9]+$', ids['browser_id'])
    
    # Check consent_id is a valid UUID
    assert re.match(r'^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$', ids['consent_id'])
    
    # Check gcl_au format
    assert re.match(r'^1\.1\.\d{10}\.\d+$', ids['gcl_au'])


def test_format_cookie_parts():
    now = datetime(2023, 1, 1, 12, 0, 0)
    iso_encoded = "2023-01-01T12%3A00%3A00.000Z"
    unix_now = 1672574400000
    unix_yesterday = 1672488000000
    unix_tomorrow = 1672660800000
    
    ids = {
        'browser_id': 'abcdef1234567890abcdef12',
        'consent_id': '12345678-1234-1234-1234-1234567890ab',
        'gcl_au': '1.1.1234567890.1672574400000',
        'pdst_id': '0123456789abcdef0123456789abcdef',
        'scor_uid': '0123456789abcdef0123456789abcdef',
        'gid_value': 'GA1.2.1234567890.1672574400000',
        'tt_value': 'ABCDEFGHIJKLMNOPQRSTUVWX',
        'ga_value': 'GA1.2.1234567890.1672574400000',
        'uetsid': '0123456789abcdef0123456789abcdef|a|2|fvw|0|1959',
        'uetvid': '0123456789abcdef0123456789abcdef|a|1672574400000|1|1|bat.bing.com/p/conversions/c/a',
        'ttcsid_id': 'ABCDEFGHIJKLMNOPQRST',
        'waf_token': '12345678-1234-1234-1234-1234567890ab:BQoAqBA15hAsAAAA:abcdefghijklmnopqrstuvwxyz'
    }
    
    result = format_cookie_parts(now, iso_encoded, unix_now, unix_yesterday, unix_tomorrow, ids)
    
    # Check return type
    assert isinstance(result, list)
    
    # Check expected number of elements
    assert len(result) > 20  # We expect many cookie parts
    
    # Check a few specific elements
    assert f"RF_BROWSER_ID={ids['browser_id']}" in result
    assert "_gcl_au=" in result[3]
    assert "_tt_enable_cookie=1" in result


def test_generate_dynamic_cookie():
    cookie = generate_dynamic_cookie()
    
    # Check it's a string
    assert isinstance(cookie, str)
    
    # Check semicolon-separated format
    parts = cookie.split("; ")
    assert len(parts) > 20  # Many cookie parts
    
    # Check for common cookie components
    assert any(part.startswith("RF_BROWSER_ID=") for part in parts)
    assert any(part.startswith("_gcl_au=") for part in parts)
    assert any(part == "_tt_enable_cookie=1" for part in parts)


def test_get_random_user_agent():
    ua = get_random_user_agent()
    
    # Check it's a string
    assert isinstance(ua, str)
    
    # Check it contains expected user agent components
    assert any(browser in ua for browser in ["Chrome", "Safari"])
    assert any(os in ua for os in ["Windows", "Macintosh", "Linux"])


def test_build_city_code_params():
    params = build_city_code_params("Austin, TX")
    
    assert params["location"] == "Austin, TX"
    assert params["start"] == "0"
    assert params["count"] == "10"
    assert params["v"] == "2"
    assert params["iss"] == "false"
    assert params["ooa"] == "true"


def test_extract_scripts_from_page():
    html = """
    <html>
    <head>
        <script>some script</script>
        <script>_tLAB.wait(function() { console.log('test1'); });</script>
        <script>another script</script>
        <script>_tLAB.wait(function() { console.log('test2'); });</script>
    </head>
    <body>content</body>
    </html>
    """
    
    scripts = extract_scripts_from_page(html)
    
    # Check we found 2 scripts containing the specific substring
    assert len(scripts) == 2
    assert "_tLAB.wait(function() { console.log('test1'); });" in scripts
    assert "_tLAB.wait(function() { console.log('test2'); });" in scripts


def test_parse_median_prices():
    script = r'''
    _tLAB.wait(function() {
        something: [{\"label\":\"Median Sale Price\",\"aggregateData\":[{\"date\":\"2023-01-01\",\"value\":\"500,000\"},{\"date\":\"2023-02-01\",\"value\":\"510,000.50\"}]}]
    });
    '''
    
    median_prices = parse_median_prices([script])
    
    assert "2023-01" in median_prices
    assert "2023-02" in median_prices
    assert median_prices["2023-01"] == 500000
    assert median_prices["2023-02"] == 510000


def test_filter_last_3_years():
    current_year = datetime.now().year
    
    data = {
        f"{current_year-4}-01": 400000,
        f"{current_year-3}-01": 410000,
        f"{current_year-2}-01": 420000,
        f"{current_year-1}-01": 430000,
        f"{current_year}-01": 440000,
    }
    
    filtered = filter_last_3_years(data)
    
    # Oldest two dates removed
    assert f"{current_year-4}-01" not in filtered
    assert f"{current_year-3}-01" not in filtered
    
    # Check all recent dates are kept
    assert f"{current_year-2}-01" in filtered
    assert f"{current_year-1}-01" in filtered
    assert f"{current_year}-01" in filtered
    
    # Check values are preserved
    assert filtered[f"{current_year}-01"] == 440000
