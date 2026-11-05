import os

import duckdb
import psycopg
import pytest
from psycopg import sql

from data_platform.publishing.postgres import publish_full_refresh


def test_publish_full_refresh_rolls_back_on_insert_failure(tmp_path):
    duckdb_path = tmp_path / "test.duckdb"

    with duckdb.connect(str(duckdb_path)) as source:
        source.execute(
            """
            CREATE TABLE invalid_source (
                id INTEGER,
                name VARCHAR
            )
            """
        )
        source.execute("INSERT INTO invalid_source VALUES (1, 'invalid')")

    connection_args = {
        "host": os.environ["POSTGRES_HOST"],
        "port": os.environ["POSTGRES_PORT"],
        "dbname": os.environ["POSTGRES_DB"],
        "user": os.environ["POSTGRES_USER"],
        "password": os.environ["POSTGRES_PASSWORD"],
    }

    table_name = "test_publisher_rollback"
    table_identifier = sql.Identifier("gold", table_name)

    with psycopg.connect(
        host=connection_args["host"],
        port=connection_args["port"],
        dbname=connection_args["dbname"],
        user=connection_args["user"],
        password=connection_args["password"],
    ) as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                sql.SQL(
                    "CREATE TABLE {} (id INTEGER PRIMARY KEY, name INTEGER NOT NULL)"
                ).format(table_identifier)
            )
            cursor.execute(
                sql.SQL("INSERT INTO {} VALUES (99, 100)").format(table_identifier)
            )

    try:
        with pytest.raises(psycopg.errors.InvalidTextRepresentation):
            publish_full_refresh(
                source_table="invalid_source",
                target_schema="gold",
                target_table=table_name,
                source_path=duckdb_path,
            )

        with psycopg.connect(
            host=connection_args["host"],
            port=connection_args["port"],
            dbname=connection_args["dbname"],
            user=connection_args["user"],
            password=connection_args["password"],
        ) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    sql.SQL("SELECT id, name FROM {}").format(table_identifier)
                )
                rows = cursor.fetchall()

        assert rows == [(99, 100)]

    finally:
        with psycopg.connect(
            host=connection_args["host"],
            port=connection_args["port"],
            dbname=connection_args["dbname"],
            user=connection_args["user"],
            password=connection_args["password"],
        ) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    sql.SQL("DROP TABLE IF EXISTS {}").format(table_identifier)
                )
