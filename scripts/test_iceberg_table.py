
import pyarrow as pa
import requests
from pyiceberg.catalog import load_catalog
from pyiceberg.schema import Schema
from pyiceberg.types import IntegerType, NestedField, StringType
from test_polaris_connection import (
    ENV_FILE,
    POLARIS_URL,
    REALM,
    load_local_secrets,
)

TABLE = ("bronze", "integration_test")


def main() -> None:
    secrets = load_local_secrets(ENV_FILE)

    # Authenticate with Polaris.
    response = requests.post(
        f"{POLARIS_URL}/api/catalog/v1/oauth/tokens",
        headers={"Polaris-Realm": REALM},
        auth=("root", secrets["POLARIS_CLIENT_SECRET"]),
        data={
            "grant_type": "client_credentials",
            "scope": "PRINCIPAL_ROLE:ALL",
        },
        timeout=15,
    )
    response.raise_for_status()

    catalog = load_catalog(
        "lakehouse",
        type="rest",
        uri=f"{POLARIS_URL}/api/catalog",
        warehouse="lakehouse",
        token=response.json()["access_token"],
        **{
            "header.Polaris-Realm": REALM,
            "header.X-Iceberg-Access-Delegation": "",
            "py-io-impl": "pyiceberg.io.pyarrow.PyArrowFileIO",
            "s3.endpoint": "http://127.0.0.1:9000",
            "s3.region": "us-east-1",
            "s3.access-key-id": secrets["POLARIS_S3_ACCESS_KEY"],
            "s3.secret-access-key": secrets["POLARIS_S3_SECRET_KEY"],
            "s3.force-virtual-addressing": False,
        },
    )

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

    # Append only if the test table is empty.
    existing_rows = table.scan().to_arrow().num_rows

    if existing_rows == 0:
        table.append(records)
        print("Sample records appended.")
    else:
        print(f"Table already contains {existing_rows} rows.")

    # Refresh metadata and verify persisted data.
    table = catalog.load_table(TABLE)
    result = table.scan().to_arrow()

    print("Rows returned:", result.num_rows)
    print(result.to_pydict())

    expected = {
        "id": [1, 2, 3],
        "name": ["bronze", "silver", "gold"],
    }

    if result.to_pydict() != expected:
        raise RuntimeError("Iceberg read-back validation failed.")

    print("Iceberg integration test: PASSED")


if __name__ == "__main__":
    main()
