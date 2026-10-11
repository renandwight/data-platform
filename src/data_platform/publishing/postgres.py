
import os
from pathlib import Path

import duckdb
import psycopg
from psycopg import sql


PROJECT_ROOT = Path(__file__).resolve().parents[3]
DUCKDB_PATH = PROJECT_ROOT / "dbt" / "data_platform" / "dev.duckdb"


def publish_full_refresh(
    source_table: str,
    target_schema: str,
    target_table: str,
    batch_size: int = 1000,
) -> int:
    """Replace PostgreSQL table contents in one transaction."""

    if batch_size <= 0:
        raise ValueError("batch_size must be greater than zero")

    # Use a read-only connection to the dbt development database.
    source = duckdb.connect(str(DUCKDB_PATH), read_only=True)

    try:
        # Source identifiers are quoted to avoid SQL injection.
        source_query = (
            f"SELECT * FROM {duckdb_identifier(source_table)}"
        )
        result = source.execute(source_query)
        columns = [column[0] for column in result.description]

        connection_args = {
            "host": os.environ["POSTGRES_HOST"],
            "port": os.environ["POSTGRES_PORT"],
            "dbname": os.environ["POSTGRES_DB"],
            "user": os.environ["POSTGRES_USER"],
            "password": os.environ["POSTGRES_PASSWORD"],
        }

        row_count = 0

        # Psycopg commits on success and rolls back on exception.
        with psycopg.connect(**connection_args) as target:
            with target.cursor() as cursor:
                table_identifier = sql.Identifier(
                    target_schema, target_table
                )

                cursor.execute(
                    sql.SQL("DELETE FROM {}").format(
                        table_identifier
                    )
                )

                insert_statement = sql.SQL(
                    "INSERT INTO {} ({}) VALUES ({})"
                ).format(
                    table_identifier,
                    sql.SQL(", ").join(
                        sql.Identifier(column) for column in columns
                    ),
                    sql.SQL(", ").join(
                        sql.Placeholder() for _ in columns
                    ),
                )

                while True:
                    rows = result.fetchmany(batch_size)

                    if not rows:
                        break

                    cursor.executemany(insert_statement, rows)
                    row_count += len(rows)

        return row_count

    finally:
        source.close()


def duckdb_identifier(name: str) -> str:
    """Quote a single DuckDB table identifier."""
    if not name or "." in name:
        raise ValueError(
            "Provide an unqualified DuckDB table name"
        )

    return '"' + name.replace('"', '""') + '"'