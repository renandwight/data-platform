"""HTTP client for public Socrata datasets."""

import json
from urllib.parse import urlencode
from urllib.request import Request, urlopen


def fetch_records(
    dataset_id: str,
    app_token: str = "",
    limit: int = 100,
    offset: int = 0,
    order_by: str = "row_key",
) -> list[dict]:
    """Fetch a page of JSON records from a Socrata dataset."""
    if limit < 1:
        raise ValueError("limit must be greater than zero")

    if offset < 0:
        raise ValueError("offset must not be negative")

    query = urlencode(
        {
            "$limit": limit,
            "$offset": offset,
            "$order": order_by,
        }
    )

    url = f"https://data.austintexas.gov/resource/{dataset_id}.json?{query}"

    headers = {"Accept": "application/json"}

    if app_token:
        headers["X-App-Token"] = app_token

    request = Request(url, headers=headers)

    with urlopen(request, timeout=30) as response:
        records = json.load(response)

    if not isinstance(records, list):
        raise TypeError("Expected a JSON array from Socrata")

    return records


def fetch_all_records(
    dataset_id: str,
    app_token: str = "",
    page_size: int = 100,
    order_by: str = "row_key",
) -> list[dict]:
    """Fetch all records using deterministic pagination."""
    if page_size < 1:
        raise ValueError("page_size must be greater than zero")

    records = []
    offset = 0

    while True:
        page = fetch_records(
            dataset_id=dataset_id,
            app_token=app_token,
            limit=page_size,
            offset=offset,
            order_by=order_by,
        )

        records.extend(page)

        if len(page) < page_size:
            break

        offset += len(page)

    return records
