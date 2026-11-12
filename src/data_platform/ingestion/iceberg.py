"""Reusable Iceberg full-snapshot publishing utilities."""

import pyarrow as pa
from pyiceberg.catalog import Catalog
from pyiceberg.schema import Schema
from pyiceberg.types import (
    BooleanType,
    DecimalType,
    DoubleType,
    IntegerType,
    LongType,
    NestedField,
    StringType,
    TimestamptzType,
)


def arrow_to_iceberg_schema(schema: pa.Schema) -> Schema:
    """Convert a flat Arrow schema into an Iceberg schema."""
    fields = []

    for field_id, field in enumerate(schema, start=1):
        data_type = field.type

        if pa.types.is_string(data_type):
            iceberg_type = StringType()
        elif pa.types.is_int32(data_type):
            iceberg_type = IntegerType()
        elif pa.types.is_int64(data_type):
            iceberg_type = LongType()
        elif pa.types.is_boolean(data_type):
            iceberg_type = BooleanType()
        elif pa.types.is_float64(data_type):
            iceberg_type = DoubleType()
        elif pa.types.is_decimal(data_type):
            iceberg_type = DecimalType(
                precision=data_type.precision,
                scale=data_type.scale,
            )
        elif pa.types.is_timestamp(data_type) and data_type.tz is not None:
            if data_type.unit != "us":
                raise ValueError("Only microsecond timestamps are supported")
            iceberg_type = TimestamptzType()
        else:
            raise ValueError(f"Unsupported Arrow type: {data_type}")

        fields.append(
            NestedField(
                field_id=field_id,
                name=field.name,
                field_type=iceberg_type,
                required=not field.nullable,
            )
        )

    return Schema(*fields)


def overwrite_iceberg_table(
    catalog: Catalog,
    identifier: tuple[str, str],
    records: pa.Table,
) -> None:
    """Validate and publish a complete Iceberg snapshot."""
    if records.num_rows == 0:
        raise ValueError("Refusing to overwrite Iceberg with zero records")

    iceberg_schema = arrow_to_iceberg_schema(records.schema)

    if catalog.table_exists(identifier):
        table = catalog.load_table(identifier)

        existing_schema = table.schema()

        if (
            [(field.name, field.field_type, field.required) for field in existing_schema.fields]
            != [(field.name, field.field_type, field.required) for field in iceberg_schema.fields]
        ):
            raise ValueError(
                f"Existing Iceberg schema differs from incoming schema: {identifier}"
            )
    else:
        table = catalog.create_table(
            identifier=identifier,
            schema=iceberg_schema,
        )

    table.overwrite(records)

    persisted = catalog.load_table(identifier).scan().to_arrow()

    if persisted.num_rows != records.num_rows:
        raise RuntimeError(
            f"Persisted row count mismatch: "
            f"expected {records.num_rows}, got {persisted.num_rows}"
        )

    if "row_key" in records.column_names:
        expected_keys = set(records.column("row_key").to_pylist())
        actual_keys = set(persisted.column("row_key").to_pylist())

        if actual_keys != expected_keys:
            raise RuntimeError("Persisted Iceberg row keys do not match")