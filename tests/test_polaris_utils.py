"""Unit tests for reusable Polaris connections."""

from unittest.mock import Mock, patch

import pytest
import requests

from data_platform.config.settings import Settings
from data_platform.connections.polaris import (
    create_iceberg_catalog,
    get_polaris_token,
)


@pytest.fixture
def settings():
    return Settings(
        polaris_url="http://127.0.0.1:8181",
        polaris_realm="POLARIS",
        polaris_catalog="lakehouse",
        polaris_warehouse="lakehouse",
        polaris_client_id="root",
        polaris_client_secret="test-secret",
        minio_endpoint="http://127.0.0.1:9000",
        minio_region="us-east-1",
        minio_access_key="test-access",
        minio_secret_key="test-key",
    )


@patch("data_platform.connections.polaris.requests.post")
def test_get_polaris_token(mock_post, settings):
    response = Mock()
    response.json.return_value = {"access_token": "test-token"}
    mock_post.return_value = response

    token = get_polaris_token(settings)

    assert token == "test-token"
    response.raise_for_status.assert_called_once()

    mock_post.assert_called_once_with(
        "http://127.0.0.1:8181/api/catalog/v1/oauth/tokens",
        headers={"Polaris-Realm": "POLARIS"},
        auth=("root", "test-secret"),
        data={
            "grant_type": "client_credentials",
            "scope": "PRINCIPAL_ROLE:ALL",
        },
        timeout=15,
    )


@patch("data_platform.connections.polaris.requests.post")
def test_authentication_failure(mock_post, settings):
    response = Mock()
    response.raise_for_status.side_effect = requests.HTTPError("Authentication failed")
    mock_post.return_value = response

    with pytest.raises(requests.HTTPError):
        get_polaris_token(settings)


@patch("data_platform.connections.polaris.requests.post")
def test_missing_access_token(mock_post, settings):
    response = Mock()
    response.json.return_value = {"access_token": ""}
    mock_post.return_value = response

    with pytest.raises(ValueError, match="invalid access token"):
        get_polaris_token(settings)


@patch("data_platform.connections.polaris.load_catalog")
@patch("data_platform.connections.polaris.get_polaris_token")
def test_create_iceberg_catalog(mock_token, mock_catalog, settings):
    mock_token.return_value = "test-token"

    catalog = create_iceberg_catalog(settings)

    assert catalog is mock_catalog.return_value
    mock_token.assert_called_once_with(settings)

    args, kwargs = mock_catalog.call_args

    assert args == ("lakehouse",)
    assert kwargs["type"] == "rest"
    assert kwargs["warehouse"] == "lakehouse"
    assert kwargs["token"] == "test-token"
    assert kwargs["header.Polaris-Realm"] == "POLARIS"
    assert kwargs["header.X-Iceberg-Access-Delegation"] == ""
    assert kwargs["s3.access-key-id"] == "test-access"
    assert kwargs["s3.secret-access-key"] == "test-key"
    assert kwargs["s3.force-virtual-addressing"] is False
