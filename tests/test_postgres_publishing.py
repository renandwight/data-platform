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

    with psycopg.connect(**connection_args) as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT COUNT(*) FROM gold.dim_customers"
            )
            original_count = cursor.fetchone()[0]

    with pytest.raises(RuntimeError):
        with psycopg.connect(**connection_args) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    "DELETE FROM gold.dim_customers"
                )

                raise RuntimeError(
                    "Simulated failure before commit"
                )

    with psycopg.connect(**connection_args) as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT COUNT(*) FROM gold.dim_customers"
            )
            final_count = cursor.fetchone()[0]

    assert final_count == original_count