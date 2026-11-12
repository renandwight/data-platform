"""Transform Contracts Bronze data into Silver Iceberg records."""

from data_platform.config.settings import load_settings
from data_platform.connections.duckdb import (
    attach_polaris_catalog,
    configure_minio,
    create_duckdb_connection,
)
from data_platform.transformations.contracts import (
    transform_contracts_to_silver,
)

from data_platform.connections.polaris import create_iceberg_catalog
from data_platform.ingestion.iceberg import overwrite_iceberg_table


def main() -> None:
    settings = load_settings()
    con = create_duckdb_connection()

    try:
        configure_minio(con, settings)
        attach_polaris_catalog(con, settings)

        con.execute(
            """
            CREATE TEMP VIEW bronze_source AS
            SELECT *
            FROM polaris.bronze.contracts
            """
        )

        print("Transforming Contracts Bronze records...")

        records = transform_contracts_to_silver(con)

        print(f"Records transformed: {records.num_rows}")
        print("\nSilver Arrow schema:")
        print(records.schema)

        print("\nData quality summary:")

        con.register("silver_preview", records)

        con.sql(
            """
            SELECT
                COUNT(*) AS total_records,
                COUNT(DISTINCT row_key) AS unique_keys,
                COUNT(*) FILTER (
                    WHERE brd_awd_dt_invalid
                ) AS invalid_award_dates
            FROM silver_preview
            """
        ).show()

        print("\nPublishing Contracts Silver snapshot...")

        catalog = create_iceberg_catalog(settings)

        overwrite_iceberg_table(
            catalog=catalog,
            identifier=("silver", "contracts"),
            records=records,
        )

        print("Silver Iceberg table: silver.contracts")
        print(f"Records persisted: {records.num_rows}")
        print("Contracts Silver transformation: PASSED")

    finally:
        con.close()


if __name__ == "__main__":
    main()