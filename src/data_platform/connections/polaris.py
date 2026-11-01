
"""Reusable Apache Polaris authentication and PyIceberg connections."""

import requests
from pyiceberg.catalog import Catalog, load_catalog

from data_platform.config.settings import Settings


def get_polaris_token(settings: Settings) -> str:
    """Authenticate with Polaris using OAuth client credentials."""
    response = requests.post(
        f"{settings.polaris_url.rstrip('/')}/api/catalog/v1/oauth/tokens",
        headers={"Polaris-Realm": settings.polaris_realm},
        auth=(
            settings.polaris_client_id,
            settings.polaris_client_secret,
        ),
        data={
            "grant_type": "client_credentials",
            "scope": "PRINCIPAL_ROLE:ALL",
        },
        timeout=15,
    )

    response.raise_for_status()
    token = response.json()["access_token"]

    if not isinstance(token, str) or not token:
        raise ValueError("Polaris returned an invalid access token")

    return token


def create_iceberg_catalog(settings: Settings) -> Catalog:
    """Create an authenticated PyIceberg REST catalog."""
    token = get_polaris_token(settings)

    return load_catalog(
        settings.polaris_catalog,
        type="rest",
        uri=f"{settings.polaris_url.rstrip('/')}/api/catalog",
        warehouse=settings.polaris_warehouse,
        token=token,
        **{
            "header.Polaris-Realm": settings.polaris_realm,
            "header.X-Iceberg-Access-Delegation": "",
            "py-io-impl": "pyiceberg.io.pyarrow.PyArrowFileIO",
            "s3.endpoint": settings.minio_endpoint,
            "s3.region": settings.minio_region,
            "s3.access-key-id": settings.minio_access_key,
            "s3.secret-access-key": settings.minio_secret_key,
            "s3.force-virtual-addressing": False,
        },
    )
