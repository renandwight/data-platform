
import argparse

from data_platform.publishing.postgres import publish_full_refresh


def main():
    parser = argparse.ArgumentParser(
        description="Publish a DuckDB model to PostgreSQL Gold."
    )

    parser.add_argument("--source", required=True)
    parser.add_argument("--schema", default="gold")
    parser.add_argument("--table", required=True)

    args = parser.parse_args()

    count = publish_full_refresh(
        source_table=args.source,
        target_schema=args.schema,
        target_table=args.table,
    )

    print(f"Successfully published {count} rows to {args.schema}.{args.table}")


if __name__ == "__main__":
    main()