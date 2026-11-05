"""Configure dbt-duckdb connections for Polaris-managed Iceberg."""

from typing import Any

from dbt.adapters.duckdb.plugins import BasePlugin
from duckdb import DuckDBPyConnection

from data_platform.config.settings import load_settings
from data_platform.connections.duckdb import (
    attach_polaris_catalog,
    configure_minio,
)


class Plugin(BasePlugin):
    """Configure DuckDB access to MinIO and Apache Polaris."""

    def initialize(self, plugin_config: dict[str, Any]) -> None:
        """Load the shared data platform configuration."""
        self.settings = load_settings()

    def configure_connection(self, conn: DuckDBPyConnection) -> None:
        """Configure the DuckDB connection managed by dbt."""
        conn.execute("LOAD iceberg")
        conn.execute("LOAD httpfs")

        configure_minio(conn, self.settings)
        attach_polaris_catalog(conn, self.settings)
