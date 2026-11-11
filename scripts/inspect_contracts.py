"""Inspect Contracts API field consistency."""

from collections import Counter

from data_platform.config.settings import load_settings
from data_platform.connections.socrata import fetch_all_records


def main() -> None:
    settings = load_settings()

    records = fetch_all_records(
        dataset_id="84ih-p28j",
        app_token=settings.socrata_app_token,
        page_size=100,
        order_by="row_key",
    )

    field_counts = Counter(field for record in records for field in record)

    print(f"Records: {len(records)}")
    print(f"Fields returned by API: {len(field_counts)}")

    print("\nFields with missing values:")
    for field, count in sorted(field_counts.items()):
        if count < len(records):
            print(f"{field}: {len(records) - count} missing")


if __name__ == "__main__":
    main()
