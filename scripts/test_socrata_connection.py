"""Verify paginated extraction from the Contracts API."""

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

    keys = [record["row_key"] for record in records]

    print(f"Retrieved records: {len(records)}")
    print(f"Unique row keys: {len(set(keys))}")
    print(f"Duplicate row keys: {len(keys) - len(set(keys))}")


if __name__ == "__main__":
    main()
