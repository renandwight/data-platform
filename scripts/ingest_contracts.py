"""Ingest City of Austin Contracts into Bronze Iceberg."""

from data_platform.config.settings import load_settings
from data_platform.connections.polaris import create_iceberg_catalog
from data_platform.connections.socrata import fetch_all_records
from data_platform.ingestion.contracts import (
    CONTRACTS_DATASET_ID,
    CONTRACTS_TABLE,
    prepare_contracts,
)
from data_platform.ingestion.iceberg import overwrite_iceberg_table


def main() -> None:
    settings = load_settings()

    print("Fetching Contracts records from Socrata...")

    records = fetch_all_records(
        dataset_id=CONTRACTS_DATASET_ID,
        app_token=settings.socrata_app_token,
        page_size=100,
        order_by="row_key",
    )

    print(f"Records extracted: {len(records)}")

    arrow_table = prepare_contracts(records)

    print(f"Records validated: {arrow_table.num_rows}")
    print(f"Columns prepared: {arrow_table.num_columns}")

    catalog = create_iceberg_catalog(settings)

    overwrite_iceberg_table(
        catalog=catalog,
        identifier=CONTRACTS_TABLE,
        records=arrow_table,
    )

    print("Bronze Iceberg table: bronze.contracts")
    print(f"Records persisted: {arrow_table.num_rows}")
    print("Contracts Bronze ingestion: PASSED")


if __name__ == "__main__":
    main()