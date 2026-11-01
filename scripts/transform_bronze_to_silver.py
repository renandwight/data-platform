
"""Transform Bronze Iceberg data and persist it into Silver."""

import pyarrow as pa
from pyiceberg.schema import Schema
from pyiceberg.types import IntegerType, NestedField, StringType

from data_platform.config.settings import load_settings
from data_platform.connections.duckdb import (
    attach_polaris_catalog,
    configure_minio,
    create_duckdb_connection,
)
from data_platform.connections.polaris import create_iceberg_catalog
from data_platform.transformations.bronze_to_silver import (
    transform_bronze_to_silver,
)

SOURCE_TABLE = ("bronze", "integration_test")
TARGET_TABLE = ("silver", "integration_test")


def main() -> None:
    settings = load_settings()
    con = create_duckdb_connection()

    try:
        configure_minio(con, settings)
        attach_polaris_catalog(con, settings)

        # Register the existing Bronze Iceberg table as a DuckDB view.
        con.execute(
            """
            CREATE TEMP VIEW bronze_source AS
            SELECT id, name
            FROM polaris.bronze.integration_test
            """
        )

        # Apply reusable validation and transformation logic.
        rows = transform_bronze_to_silver(con)

        source_count = len(rows)

        print("Bronze records transformed:", source_count)

    finally:
        con.close()

    # Convert DuckDB results to a typed Arrow table.
    arrow_schema = pa.schema(
        [
            pa.field("id", pa.int32(), nullable=False),
            pa.field("name", pa.string(), nullable=False),
            pa.field("name_length", pa.int32(), nullable=False),
        ]
    )

    records = pa.Table.from_pylist(
        [
            {
                "id": row[0],
                "name": row[1],
                "name_length": row[2],
            }
            for row in rows
        ],
        schema=arrow_schema,
    )

    # Connect to the Polaris-managed Iceberg catalog.
    catalog = create_iceberg_catalog(settings)

    iceberg_schema = Schema(
        NestedField(
            field_id=1,
            name="id",
            field_type=IntegerType(),
            required=True,
        ),
        NestedField(
            field_id=2,
            name="name",
            field_type=StringType(),
            required=True,
        ),
        NestedField(
            field_id=3,
            name="name_length",
            field_type=IntegerType(),
            required=True,
        ),
    )

    if catalog.table_exists(TARGET_TABLE):
        print("Silver table already exists; loading it.")
        table = catalog.load_table(TARGET_TABLE)
    else:
        table = catalog.create_table(
            identifier=TARGET_TABLE,
            schema=iceberg_schema,
        )
        print("Silver table created.")

    # Replace Silver data instead of appending duplicates.
    table.overwrite(records)
    print("Silver records written:", records.num_rows)

    # Reload the table to verify persisted records.
    table = catalog.load_table(TARGET_TABLE)
    result = table.scan().to_arrow()

    actual = sorted(
        zip(
            result.column("id").to_pylist(),
            result.column("name").to_pylist(),
            result.column("name_length").to_pylist(),
        )
    )

    if actual != rows:
        raise RuntimeError(
            "Silver read-back validation failed: "
            "persisted records do not match transformed records"
        )

    print("Silver records:", actual)
    print("Bronze-to-Silver persistence: PASSED")


if __name__ == "__main__":
    main()
