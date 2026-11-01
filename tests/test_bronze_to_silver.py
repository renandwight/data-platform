
"""Unit tests for Bronze-to-Silver transformations."""

import duckdb
import pytest

from data_platform.transformations.bronze_to_silver import (
    transform_bronze_to_silver,
)


@pytest.fixture
def con():
    connection = duckdb.connect(":memory:")

    yield connection

    connection.close()


def test_valid_transformation(con):
    con.execute(
        """
        CREATE TABLE bronze_source (
            id INTEGER,
            name VARCHAR
        )
        """
    )

    con.execute(
        """
        INSERT INTO bronze_source VALUES
            (1, ' bronze '),
            (2, 'silver'),
            (3, 'gold')
        """
    )

    result = transform_bronze_to_silver(con)

    assert result == [
        (1, "BRONZE", 6),
        (2, "SILVER", 6),
        (3, "GOLD", 4),
    ]


@pytest.mark.parametrize(
    "records",
    [
        [(None, "bronze")],
        [(1, None)],
        [(1, "")],
        [(1, "   ")],
        [(1, "bronze"), (1, "silver")],
    ],
)
def test_invalid_source_rejected(con, records):
    con.execute(
        """
        CREATE TABLE bronze_source (
            id INTEGER,
            name VARCHAR
        )
        """
    )

    con.executemany(
        "INSERT INTO bronze_source VALUES (?, ?)",
        records,
    )

    with pytest.raises(ValueError, match="quality validation failed"):
        transform_bronze_to_silver(con)
