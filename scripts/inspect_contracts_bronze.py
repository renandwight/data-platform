"""Inspect Contracts Bronze values before Silver modeling."""

from data_platform.config.settings import load_settings
from data_platform.connections.duckdb import (
    attach_polaris_catalog,
    configure_minio,
    create_duckdb_connection,
)


def main() -> None:
    settings = load_settings()
    con = create_duckdb_connection()

    try:
        configure_minio(con, settings)
        attach_polaris_catalog(con, settings)

        print("Financial amount samples:")
        con.sql(
            """
            SELECT
                ma_prch_lmt_am,
                ma_itd_ord_am,
                ma_do_rfed_am
            FROM polaris.bronze.contracts
            LIMIT 5
            """
        ).show()

        print("\nBoard award date year distribution:")
        con.sql(
            """
            SELECT
                LEFT(brd_awd_dt, 4) AS award_year,
                COUNT(*) AS records
            FROM polaris.bronze.contracts
            GROUP BY 1
            ORDER BY 1
            """
        ).show()

        print("\nNumeric conversion failures:")
        con.sql(
            """
            SELECT
                COUNT(*) FILTER (
                    WHERE ma_prch_lmt_am IS NOT NULL
                      AND TRY_CAST(ma_prch_lmt_am AS DECIMAL(18,2)) IS NULL
                ) AS purchase_limit_failures,
                COUNT(*) FILTER (
                    WHERE ma_itd_ord_am IS NOT NULL
                      AND TRY_CAST(ma_itd_ord_am AS DECIMAL(18,2)) IS NULL
                ) AS ordered_amount_failures,
                COUNT(*) FILTER (
                    WHERE ma_do_rfed_am IS NOT NULL
                      AND TRY_CAST(ma_do_rfed_am AS DECIMAL(18,2)) IS NULL
                ) AS referenced_amount_failures
            FROM polaris.bronze.contracts
            """
        ).show()

        print("\nEffective date year distributions:")
        con.sql(
            """
            SELECT
                'efbgn_dt' AS field_name,
                LEFT(efbgn_dt, 4) AS year,
                COUNT(*) AS records
            FROM polaris.bronze.contracts
            GROUP BY 1, 2

            UNION ALL

            SELECT
                'efend_dt' AS field_name,
                LEFT(efend_dt, 4) AS year,
                COUNT(*) AS records
            FROM polaris.bronze.contracts
            GROUP BY 1, 2

            ORDER BY field_name, year
            """
        ).show()

    finally:
        con.close()


if __name__ == "__main__":
    main()