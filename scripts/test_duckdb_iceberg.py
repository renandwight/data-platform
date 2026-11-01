

import duckdb
import requests
from test_polaris_connection import (
    ENV_FILE,
    POLARIS_URL,
    REALM,
    load_local_secrets,
)


def main():
    secrets = load_local_secrets(ENV_FILE)

    response = requests.post(
        f"{POLARIS_URL}/api/catalog/v1/oauth/tokens",
        auth=("root", secrets["POLARIS_CLIENT_SECRET"]),
        headers={"Polaris-Realm": REALM},
        data={
            "grant_type": "client_credentials",
            "scope": "PRINCIPAL_ROLE:ALL",
        },
        timeout=15,
    )
    response.raise_for_status()
    token = response.json()["access_token"]

    con = duckdb.connect()
    con.execute("LOAD iceberg")
    con.execute("LOAD httpfs")

    # Temporary S3 credentials for our existing MinIO bucket.
    con.execute(
        """
        CREATE SECRET minio_iceberg (
            TYPE S3,
            KEY_ID ?,
            SECRET ?,
            REGION 'us-east-1',
            ENDPOINT '127.0.0.1:9000',
            URL_STYLE 'path',
            USE_SSL false,
            SCOPE 's3://iceberg/'
        )
        """,
        [
            secrets["POLARIS_S3_ACCESS_KEY"],
            secrets["POLARIS_S3_SECRET_KEY"],
        ],
    )

    # Connect to the existing Polaris Iceberg REST catalog.
    con.execute(
        """
        ATTACH 'lakehouse' AS polaris (
            TYPE ICEBERG,
            ENDPOINT 'http://127.0.0.1:8181/api/catalog',
            TOKEN ?,
            ACCESS_DELEGATION_MODE 'none',
            EXTRA_HTTP_HEADERS MAP {
                'Polaris-Realm': 'POLARIS'
            }
        )
        """,
        [token],
    )

    print("Catalogs:", con.execute("SHOW DATABASES").fetchall())
    print("Tables:", con.execute("SHOW ALL TABLES").fetchall())

    rows = con.execute(
        """
        SELECT id, name
        FROM polaris.bronze.integration_test
        ORDER BY id
        """
    ).fetchall()

    print("Iceberg records:", rows)

    expected = [(1, "bronze"), (2, "silver"), (3, "gold")]
    assert rows == expected, f"Unexpected records: {rows}"

    print("DuckDB Iceberg integration test: PASSED")
    con.close()


if __name__ == "__main__":
    main()
