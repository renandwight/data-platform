"""Unit tests for Iceberg snapshot publishing."""

from unittest.mock import MagicMock

import pyarrow as pa
import pytest
from pyiceberg.types import DecimalType

from data_platform.ingestion.iceberg import (
    arrow_to_iceberg_schema,
    overwrite_iceberg_table,
)


def make_records() -> pa.Table:
    """Create a small Arrow table with a unique row key."""
    return pa.table(
        {
            "row_key": ["contract-1", "contract-2"],
            "doc_id": ["123", "456"],
        }
    )


def test_rejects_empty_dataset():
    catalog = MagicMock()
    records = pa.table({"row_key": pa.array([], type=pa.string())})

    with pytest.raises(ValueError, match="zero records"):
        overwrite_iceberg_table(catalog, ("bronze", "contracts"), records)

    catalog.table_exists.assert_not_called()


def test_creates_new_table():
    catalog = MagicMock()
    catalog.table_exists.return_value = False

    records = make_records()
    catalog.load_table.return_value.scan.return_value.to_arrow.return_value = records

    overwrite_iceberg_table(catalog, ("bronze", "contracts"), records)

    catalog.create_table.assert_called_once()
    catalog.create_table.return_value.overwrite.assert_called_once_with(records)


def test_overwrites_existing_table():
    catalog = MagicMock()
    catalog.table_exists.return_value = True

    records = make_records()
    table = catalog.load_table.return_value
    table.schema.return_value = arrow_to_iceberg_schema(records.schema)
    table.scan.return_value.to_arrow.return_value = records

    overwrite_iceberg_table(catalog, ("bronze", "contracts"), records)

    table.overwrite.assert_called_once_with(records)
    catalog.create_table.assert_not_called()


def test_rejects_schema_mismatch():
    catalog = MagicMock()
    catalog.table_exists.return_value = True

    records = make_records()
    table = catalog.load_table.return_value

    different_schema = pa.schema([pa.field("other_column", pa.string())])
    table.schema.return_value = arrow_to_iceberg_schema(different_schema)

    with pytest.raises(ValueError, match="schema differs"):
        overwrite_iceberg_table(catalog, ("bronze", "contracts"), records)

    table.overwrite.assert_not_called()


def test_converts_decimal_schema():
    """Preserve decimal precision and scale in Iceberg."""
    arrow_schema = pa.schema(
        [
            pa.field(
                "amount",
                pa.decimal128(18, 2),
                nullable=True,
            )
        ]
    )

    iceberg_schema = arrow_to_iceberg_schema(arrow_schema)
    field = iceberg_schema.find_field("amount")

    assert field.field_type == DecimalType(
        precision=18,
        scale=2,
    )
    assert field.required is False