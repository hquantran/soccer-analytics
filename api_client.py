"""Low-level HTTP client for the API-SPORTS REST API."""

import time
from typing import Any, Iterator, Optional

import requests

from config import get_api_settings, load_config

DEFAULT_BASE_URL = "https://v3.football.api-sports.io"


def fetch_from_api(
    endpoint: str,
    params: Optional[dict] = None,
    *,
    headers: dict,
    base_url: str = DEFAULT_BASE_URL,
    safe_pause_seconds: Optional[float] = None,
    max_retries: Optional[int] = None,
) -> dict:
    """
    GET one API page with retries, pacing, and quota logging.

    Returns the parsed JSON body. Raises on HTTP errors or API-level errors.
    """
    params = params or {}
    url = f"{base_url.rstrip('/')}/{endpoint.lstrip('/')}"

    if safe_pause_seconds is None or max_retries is None:
        settings = get_api_settings(load_config())
        safe_pause_seconds = safe_pause_seconds or settings["safe_pause_seconds"]
        max_retries = max_retries if max_retries is not None else settings["max_retries"]

    last_error: Optional[Exception] = None

    for attempt in range(max_retries + 1):
        try:
            response = requests.get(url, headers=headers, params=params, timeout=30)

            if response.status_code == 429 or response.status_code >= 500:
                wait_time = 15.0 * (attempt + 1)
                print(
                    f"Status {response.status_code}. "
                    f"Retrying in {wait_time:.0f}s... "
                    f"(attempt {attempt + 1}/{max_retries})"
                )
                time.sleep(wait_time)
                continue

            response.raise_for_status()
            payload = response.json()

            errors = payload.get("errors") or {}
            if errors:
                raise RuntimeError(f"API returned errors: {errors}")

            remaining = response.headers.get("x-ratelimit-requests-remaining")
            limit = response.headers.get("x-ratelimit-requests-limit")
            if remaining and limit:
                print(f"API quota: {remaining}/{limit} requests remaining today.")

            time.sleep(safe_pause_seconds)
            return payload

        except requests.exceptions.RequestException as exc:
            last_error = exc
            if attempt == max_retries:
                raise
            time.sleep(5.0)

    if last_error:
        raise last_error
    raise RuntimeError("API request failed unexpectedly.")


def fetch_all_pages(
    endpoint: str,
    params: Optional[dict] = None,
    *,
    headers: dict,
    base_url: str = DEFAULT_BASE_URL,
    max_pages: Optional[int] = None,
    safe_pause_seconds: Optional[float] = None,
    max_retries: Optional[int] = None,
) -> Iterator[dict[str, Any]]:
    """Yield each item from a paginated endpoint's response list."""
    if max_pages is None:
        max_pages = get_api_settings(load_config()).get("max_pages")

    page = 1
    total_pages = 1

    while page <= total_pages:
        if max_pages is not None and page > max_pages:
            break

        payload = fetch_from_api(
            endpoint,
            {**(params or {}), "page": page},
            headers=headers,
            base_url=base_url,
            safe_pause_seconds=safe_pause_seconds,
            max_retries=max_retries,
        )
        total_pages = payload.get("paging", {}).get("total", 1)
        yield from payload.get("response", [])
        page += 1
