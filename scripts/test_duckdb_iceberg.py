
"""Validate DuckDB integration with Polaris-managed Iceberg tables."""

from data_platform.config.settings import load_settings
from data_platform.connections.duckdb import (
    attach_polaris_catalog,
    configure_minio,
    create_duckdb_connection,
)


def main() -> None:
    settings = load_settings()
    con = create_duckdb_connection()

    try:
        configure_minio(con, settings)
        attach_polaris_catalog(con, settings)

        print("Catalogs:", con.execute("SHOW DATABASES").fetchall())
        print("Tables:", con.execute("SHOW ALL TABLES").fetchall())

        rows = con.execute(
            """
            SELECT id, name
            FROM polaris.bronze.integration_test
            ORDER BY id
            """
        ).fetchall()

        print("Iceberg records:", rows)

        expected = [
            (1, "bronze"),
            (2, "silver"),
            (3, "gold"),
        ]

        if rows != expected:
            raise RuntimeError(
                f"Unexpected Iceberg records: {rows}"
            )

        print("DuckDB Iceberg integration test: PASSED")

    finally:
        con.close()


if __name__ == "__main__":
    main()
