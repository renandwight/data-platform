"""Unit tests for the Socrata API client."""

import io
import json
from unittest.mock import patch

import pytest

from data_platform.connections.socrata import fetch_all_records, fetch_records


def test_fetch_records_success():
    """Verify successful JSON retrieval."""
    expected = [{"row_key": "contract-1"}]

    response = io.BytesIO(json.dumps(expected).encode())

    with patch(
        "data_platform.connections.socrata.urlopen",
        return_value=response,
    ) as mock_urlopen:
        records = fetch_records(
            dataset_id="84ih-p28j",
            app_token="test-token",
            limit=3,
        )

    assert records == expected

    request = mock_urlopen.call_args.args[0]

    assert request.get_header("X-app-token") == "test-token"
    assert request.get_header("Accept") == "application/json"
    assert "$limit=3" in request.full_url or "%24limit=3" in request.full_url


def test_fetch_records_without_token():
    """Verify public requests work without an application token."""
    response = io.BytesIO(b"[]")

    with patch(
        "data_platform.connections.socrata.urlopen",
        return_value=response,
    ) as mock_urlopen:
        assert fetch_records("84ih-p28j") == []

    request = mock_urlopen.call_args.args[0]

    assert not request.has_header("X-app-token")


@pytest.mark.parametrize("limit", [0, -1])
def test_fetch_records_invalid_limit(limit):
    """Reject invalid page sizes."""
    with pytest.raises(ValueError, match="limit"):
        fetch_records("84ih-p28j", limit=limit)


def test_fetch_records_invalid_response():
    """Reject responses that are not JSON arrays."""
    response = io.BytesIO(b'{"error": "invalid response"}')

    with (
        patch(
            "data_platform.connections.socrata.urlopen",
            return_value=response,
        ),
        pytest.raises(TypeError, match="JSON array"),
    ):
        fetch_records("84ih-p28j")


def test_fetch_all_records_multiple_pages():
    """Combine multiple pages until a partial page is returned."""
    pages = [
        [{"row_key": "1"}, {"row_key": "2"}],
        [{"row_key": "3"}],
    ]

    with patch(
        "data_platform.connections.socrata.fetch_records",
        side_effect=pages,
    ) as mock_fetch:
        records = fetch_all_records("84ih-p28j", page_size=2)

    assert len(records) == 3
    assert mock_fetch.call_count == 2
    assert mock_fetch.call_args_list[0].kwargs["offset"] == 0
    assert mock_fetch.call_args_list[1].kwargs["offset"] == 2


def test_fetch_all_records_exact_page_boundary():
    """Request an additional page when the previous page is full."""
    pages = [
        [{"row_key": "1"}, {"row_key": "2"}],
        [],
    ]

    with patch(
        "data_platform.connections.socrata.fetch_records",
        side_effect=pages,
    ) as mock_fetch:
        records = fetch_all_records("84ih-p28j", page_size=2)

    assert len(records) == 2
    assert mock_fetch.call_count == 2


@pytest.mark.parametrize("page_size", [0, -1])
def test_fetch_all_records_invalid_page_size(page_size):
    """Reject invalid pagination sizes."""
    with pytest.raises(ValueError, match="page_size"):
        fetch_all_records("84ih-p28j", page_size=page_size)
