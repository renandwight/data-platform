"""Reusable DuckDB connections for Polaris-managed Iceberg tables."""

from urllib.parse import urlparse

import duckdb

from data_platform.config.settings import Settings
from data_platform.connections.polaris import get_polaris_token


def create_duckdb_connection() -> duckdb.DuckDBPyConnection:
    """Create DuckDB connection with required extensions."""
    con = duckdb.connect()

    try:
        con.execute("LOAD iceberg")
        con.execute("LOAD httpfs")
    except Exception:
        con.close()
        raise

    return con


def configure_minio(
    con: duckdb.DuckDBPyConnection,
    settings: Settings,
) -> None:
    """Configure temporary MinIO S3 credentials."""
    endpoint = urlparse(settings.minio_endpoint)

    if endpoint.scheme not in ("http", "https") or not endpoint.netloc:
        raise ValueError("Invalid MinIO endpoint")

    con.execute(
        """
        CREATE SECRET minio_iceberg (
            TYPE S3,
            KEY_ID ?,
            SECRET ?,
            REGION ?,
            ENDPOINT ?,
            URL_STYLE 'path',
            USE_SSL ?,
            SCOPE 's3://iceberg/'
        )
        """,
        [
            settings.minio_access_key,
            settings.minio_secret_key,
            settings.minio_region,
            endpoint.netloc,
            endpoint.scheme == "https",
        ],
    )


def attach_polaris_catalog(
    con: duckdb.DuckDBPyConnection,
    settings: Settings,
) -> None:
    """Attach Polaris-managed Iceberg catalog to DuckDB."""
    token = get_polaris_token(settings)

    endpoint = f"{settings.polaris_url.rstrip('/')}/api/catalog"

    def sql_literal(value: str) -> str:
        """Escape a string for use as a DuckDB SQL literal."""
        return "'" + value.replace("'", "''") + "'"

    con.execute(
        f"""
        ATTACH {sql_literal(settings.polaris_warehouse)} AS polaris (
            TYPE ICEBERG,
            ENDPOINT {sql_literal(endpoint)},
            TOKEN {sql_literal(token)},
            ACCESS_DELEGATION_MODE 'none',
            EXTRA_HTTP_HEADERS MAP {{
                'Polaris-Realm': {sql_literal(settings.polaris_realm)}
            }}
        )
        """
    )
