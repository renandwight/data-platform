import os

import psycopg
import pytest


def test_postgres_transaction_rollback():
    connection_args = {
        "host": os.environ["POSTGRES_HOST"],
        "port": os.environ["POSTGRES_PORT"],
        "dbname": os.environ["POSTGRES_DB"],
        "user": os.environ["POSTGRES_USER"],
        "password": os.environ["POSTGRES_PASSWORD"],
    }

    with psycopg.connect(
        host=connection_args["host"],
        port=connection_args["port"],
        dbname=connection_args["dbname"],
        user=connection_args["user"],
        password=connection_args["password"],
    ) as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT COUNT(*) FROM gold.dim_customers"
            )
            row = cursor.fetchone()

            if row is None:
                raise RuntimeError("Failed to retrieve original row count")

            original_count = row[0]

    with pytest.raises(RuntimeError):
        with psycopg.connect(
            host=connection_args["host"],
            port=connection_args["port"],
            dbname=connection_args["dbname"],
            user=connection_args["user"],
            password=connection_args["password"],
        ) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    "DELETE FROM gold.dim_customers"
                )

                raise RuntimeError(
                    "Simulated failure before commit"
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
                "SELECT COUNT(*) FROM gold.dim_customers"
            )
            row = cursor.fetchone()

            if row is None:
                raise RuntimeError("Failed to retrieve original row count")

            final_count = row[0]

    assert final_count == original_count