"""Bright Data SERP API Client with SQLite caching layer.

Queries the Bright Data Search Engine Results Page (SERP) API,
polls for async results, and caches responses locally for 24 hours
to avoid duplicate external requests.
"""

import asyncio
import json
import os
import sqlite3
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from urllib.parse import quote_plus

import httpx
from dotenv import load_dotenv

# Basic constants
CACHE_DB = "scrape_cache.db"
CACHE_EXPIRY_HOURS = 24


def _init_cache_db() -> None:
    """Create the cache table if it does not exist.
    
    This function should be called at the module level or during application
    startup to ensure the SQLite schema is ready.
    """
    with sqlite3.connect(CACHE_DB) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS cache (
                query     TEXT,
                location  TEXT,
                data      TEXT,
                timestamp DATETIME
            )
            """
        )
        conn.commit()


# Initialize the database on import
_init_cache_db()


def _get_cached(query: str, location: str) -> Optional[Dict[str, Any]]:
    """Return cached SERP result if it exists and is fresh (< 24 h).

    Args:
        query: Original search query string.
        location: Location string used in the search.

    Returns:
        Cached result as a dict if found and valid, otherwise None.
    """
    with sqlite3.connect(CACHE_DB) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT data, timestamp FROM cache "
            "WHERE query = ? AND location = ? "
            "ORDER BY timestamp DESC LIMIT 1",
            (query, location),
        )
        row = cursor.fetchone()
        if not row:
            return None

        data_str, timestamp_str = row
        timestamp = datetime.fromisoformat(timestamp_str)
        if datetime.now() - timestamp < timedelta(hours=CACHE_EXPIRY_HOURS):
            return json.loads(data_str)
    return None


def _save_to_cache(query: str, location: str, data: Dict[str, Any]) -> None:
    """Persist a SERP result to the SQLite cache.

    Args:
        query: Original search query string.
        location: Location string used in the search.
        data: Parsed JSON response to cache.
    """
    with sqlite3.connect(CACHE_DB) as conn:
        conn.execute(
            "INSERT INTO cache (query, location, data, timestamp) "
            "VALUES (?, ?, ?, ?)",
            (query, location, json.dumps(data), datetime.now().isoformat()),
        )
        conn.commit()


async def trigger_brightdata_scrape(
    query: str,
    location: str = "Montgomery, AL",
) -> List[Dict[str, Any]]:
    """Submit a SERP query to Bright Data and poll for results.

    Checks the local SQLite cache first. On a cache miss, submits
    the query to the Bright Data API, polls for up to 60 seconds,
    and caches the result on success.

    Args:
        query: Search query (e.g., 'pharmacy near downtown').
        location: Location context for the search.

    Returns:
        A list of search result dictionaries. Each dict contains:
            - title (str): Title of the search result.
            - link (str): Canonical URL.
            - snippet (str): Brief text description.
        If an error occurs, returns a single-item list with an 'error' key.
    """
    # Check cache first
    cached = _get_cached(query, location)
    if cached:
        organic = cached.get("organic", [])
        if organic:
            return [
                {
                    "title": r.get("title", ""),
                    "link": r.get("link", r.get("url", "")),
                    "snippet": r.get("description", r.get("snippet", "")),
                }
                for r in organic[:20]
            ]
        return []

    api_key = os.getenv("BRIGHTDATA_API_KEY", "")
    zone = os.getenv("BRIGHTDATA_ZONE", "")

    if not api_key or not zone:
        return [{"error": "BRIGHTDATA_API_KEY or BRIGHTDATA_ZONE not set"}]

    # Build the Google search URL
    encoded_query = quote_plus(f"{query} in {location}")
    google_url = f"https://www.google.com/search?q={encoded_query}"

    api_url = f"https://api.brightdata.com/serp/req?zone={zone}"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {"url": google_url}

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            # Step 1: Submit the SERP request
            response = await client.post(api_url, headers=headers, json=payload)

            if response.status_code != 200:
                return [{
                    "error": f"Bright Data API returned {response.status_code}: {response.text[:200]}"
                }]

            response_id = response.json().get("response_id")
            if not response_id:
                return [{"error": "No response_id returned from Bright Data."}]

            # Step 2: Poll for results
            poll_url = f"https://api.brightdata.com/serp/get_result?response_id={response_id}"
            poll_headers = {"Authorization": f"Bearer {api_key}"}

            for _ in range(20):
                await asyncio.sleep(3)
                poll_response = await client.get(poll_url, headers=poll_headers)

                if poll_response.status_code == 202:
                    continue  # Processing

                if poll_response.status_code != 200:
                    return [{
                        "error": f"Polling error {poll_response.status_code}: {poll_response.text[:200]}"
                    }]

                # Success
                result_data = poll_response.json()
                _save_to_cache(query, location, result_data)

                organic = result_data.get("organic", [])
                results: List[Dict[str, Any]] = []
                for item in organic[:20]:
                    results.append({
                        "title": item.get("title", ""),
                        "link": item.get("link", item.get("url", "")),
                        "snippet": item.get("description", item.get("snippet", "")),
                    })

                return results

            return [{"error": "Timed out waiting for Bright Data results."}]

    except Exception as e:
        return [{
            "error": f"Bright Data request failed: {str(e)}"
        }]
