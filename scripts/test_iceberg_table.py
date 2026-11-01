
"""Validate PyIceberg table creation, writing, and persistence."""

import pyarrow as pa
from pyiceberg.schema import Schema
from pyiceberg.types import IntegerType, NestedField, StringType

from data_platform.config.settings import load_settings
from data_platform.connections.polaris import create_iceberg_catalog

TABLE = ("bronze", "integration_test")


def main() -> None:
    settings = load_settings()
    catalog = create_iceberg_catalog(settings)

    schema = Schema(
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
            required=False,
        ),
    )

    if catalog.table_exists(TABLE):
        print("Test table already exists; loading it.")
        table = catalog.load_table(TABLE)
    else:
        table = catalog.create_table(
            identifier=TABLE,
            schema=schema,
        )
        print("Iceberg table created.")

    records = pa.Table.from_arrays(
        [
            pa.array([1, 2, 3], type=pa.int32()),
            pa.array(["bronze", "silver", "gold"], type=pa.string()),
        ],
        schema=pa.schema(
            [
                pa.field("id", pa.int32(), nullable=False),
                pa.field("name", pa.string(), nullable=True),
            ]
        ),
    )

    # Append only when the test table is empty.
    existing_rows = table.scan().to_arrow().num_rows

    if existing_rows == 0:
        table.append(records)
        print("Sample records appended.")
    else:
        print(f"Table already contains {existing_rows} rows.")

    # Reload table metadata and validate persisted records.
    table = catalog.load_table(TABLE)
    result = table.scan().to_arrow()

    print("Rows returned:", result.num_rows)
    print(result.to_pydict())

    expected = {
        "id": [1, 2, 3],
        "name": ["bronze", "silver", "gold"],
    }

    if result.to_pydict() != expected:
        raise RuntimeError(
            "Iceberg read-back validation failed."
        )

    print("Iceberg integration test: PASSED")


if __name__ == "__main__":
    main()
