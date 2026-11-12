"""Independently verify persisted Contracts Silver data."""

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

        print("Silver data quality:")
        con.sql(
            """
            SELECT
                COUNT(*) AS total_records,
                COUNT(DISTINCT row_key) AS unique_keys,
                COUNT(*) FILTER (
                    WHERE brd_awd_dt_invalid
                ) AS invalid_award_dates,
                COUNT(*) FILTER (
                    WHERE brd_awd_dt IS NOT NULL
                ) AS valid_award_dates,
                COUNT(*) FILTER (
                    WHERE efend_dt IS NULL
                ) AS missing_end_dates
            FROM polaris.silver.contracts
            """
        ).show()

        print("\nFinancial and timestamp samples:")
        con.sql(
            """
            SELECT
                row_key,
                ma_prch_lmt_am,
                ma_itd_ord_am,
                ma_do_rfed_am,
                efbgn_dt,
                _ingested_at
            FROM polaris.silver.contracts
            ORDER BY row_key
            LIMIT 5
            """
        ).show()

        print("\nContract document-version relationships:")
        con.sql(
            """
            WITH document_versions AS (
                SELECT
                    doc_cd,
                    doc_dept_cd,
                    doc_id,
                    doc_vers_no,
                    COUNT(*) AS vendor_lines,
                    COUNT(DISTINCT vend_cust_cd) AS distinct_vendors,
                    COUNT(DISTINCT doc_vend_ln_no) AS distinct_line_numbers
                FROM polaris.silver.contracts
                GROUP BY
                    doc_cd,
                    doc_dept_cd,
                    doc_id,
                    doc_vers_no
            )
            SELECT
                COUNT(*) AS document_versions,
                SUM(vendor_lines) AS total_records,
                COUNT(*) FILTER (
                    WHERE vendor_lines > 1
                ) AS multi_vendor_versions,
                MAX(vendor_lines) AS max_lines_per_version,
                COUNT(*) FILTER (
                    WHERE vendor_lines <> distinct_vendors
                ) AS versions_with_repeated_vendors,
                COUNT(*) FILTER (
                    WHERE vendor_lines <> distinct_line_numbers
                ) AS versions_with_repeated_line_numbers
            FROM document_versions
            """
        ).show()

        print("\nROW_KEY construction validation:")
        con.sql(
            """
            SELECT
                COUNT(*) AS total_records,
                COUNT(*) FILTER (
                    WHERE row_key = CONCAT(
                        doc_cd,
                        doc_dept_cd,
                        doc_id,
                        CAST(doc_vers_no AS VARCHAR),
                        vend_cust_cd
                    )
                ) AS matching_keys
            FROM polaris.silver.contracts
            """
        ).show()

        print("\nContract document version profiling:")
        con.sql(
            """
            WITH documents AS (
                SELECT
                    doc_cd,
                    doc_dept_cd,
                    doc_id,
                    COUNT(DISTINCT doc_vers_no) AS version_count,
                    COUNT(*) AS record_count
                FROM polaris.silver.contracts
                GROUP BY
                    doc_cd,
                    doc_dept_cd,
                    doc_id
            )
            SELECT
                COUNT(*) AS distinct_documents,
                COUNT(*) FILTER (
                    WHERE version_count > 1
                ) AS documents_with_multiple_versions,
                MAX(version_count) AS max_versions_per_document,
                MAX(record_count) AS max_records_per_document
            FROM documents
            """
        ).show()

        print("\nFinancial amount consistency by document version:")
        con.sql(
            """
            WITH document_versions AS (
                SELECT
                    doc_cd,
                    doc_dept_cd,
                    doc_id,
                    doc_vers_no,
                    COUNT(*) AS line_count,
                    COUNT(DISTINCT ma_prch_lmt_am) AS purchase_limit_values,
                    COUNT(DISTINCT ma_itd_ord_am) AS ordered_amount_values,
                    COUNT(DISTINCT ma_do_rfed_am) AS referenced_amount_values
                FROM polaris.silver.contracts
                GROUP BY
                    doc_cd,
                    doc_dept_cd,
                    doc_id,
                    doc_vers_no
            )
            SELECT
                COUNT(*) FILTER (
                    WHERE line_count > 1
                ) AS multi_line_groups,
                COUNT(*) FILTER (
                    WHERE line_count > 1
                      AND purchase_limit_values = 1
                ) AS same_purchase_limit,
                COUNT(*) FILTER (
                    WHERE line_count > 1
                      AND ordered_amount_values = 1
                ) AS same_ordered_amount,
                COUNT(*) FILTER (
                    WHERE line_count > 1
                      AND referenced_amount_values = 1
                ) AS same_referenced_amount
            FROM document_versions
            """
        ).show()

        print("\nDocument financial grain validation:")
        con.sql(
            """
            WITH financial_combinations AS (
                SELECT DISTINCT
                    doc_cd,
                    doc_dept_cd,
                    doc_id,
                    doc_vers_no,
                    ma_prch_lmt_am,
                    ma_itd_ord_am,
                    ma_do_rfed_am
                FROM polaris.silver.contracts
            ),
            document_checks AS (
                SELECT
                    doc_cd,
                    doc_dept_cd,
                    doc_id,
                    doc_vers_no,
                    COUNT(*) AS financial_combinations
                FROM financial_combinations
                GROUP BY
                    doc_cd,
                    doc_dept_cd,
                    doc_id,
                    doc_vers_no
            )
            SELECT
                COUNT(*) AS documents_checked,
                COUNT(*) FILTER (
                    WHERE financial_combinations > 1
                ) AS inconsistent_documents
            FROM document_checks
            """
        ).show()

    finally:
        con.close()


if __name__ == "__main__":
    main()