"""Contracts Bronze-to-Silver transformation definitions."""

import pyarrow as pa

CONTRACTS_SILVER_SQL = """
SELECT
    row_key,
    doc_cd,
    doc_dept_cd,
    doc_id,
    TRY_CAST(doc_vers_no AS INTEGER) AS doc_vers_no,
    NULLIF(TRIM(doc_dscr), '') AS doc_dscr,
    contract_synopsis,
    contract_contact_nm,
    contract_contact_voice_ph_no,
    contract_contact_email_ad,

    TRY_CAST(ma_prch_lmt_am AS DECIMAL(18,2)) AS ma_prch_lmt_am,
    TRY_CAST(ma_itd_ord_am AS DECIMAL(18,2)) AS ma_itd_ord_am,
    TRY_CAST(ma_do_rfed_am AS DECIMAL(18,2)) AS ma_do_rfed_am,

    TRY_CAST(efbgn_dt AS TIMESTAMPTZ) AS efbgn_dt,
    TRY_CAST(efend_dt AS TIMESTAMPTZ) AS efend_dt,

    gnrc_po_rpt_1,
    rpt_dscr,

    brd_awd_dt AS brd_awd_dt_raw,

    CASE
        WHEN TRY_CAST(LEFT(brd_awd_dt, 4) AS INTEGER)
             BETWEEN 2000 AND 2100
        THEN TRY_CAST(brd_awd_dt AS TIMESTAMPTZ)
        ELSE NULL
    END AS brd_awd_dt,

    CASE
        WHEN brd_awd_dt IS NULL THEN FALSE
        WHEN TRY_CAST(LEFT(brd_awd_dt, 4) AS INTEGER)
             BETWEEN 2000 AND 2100
             AND TRY_CAST(brd_awd_dt AS TIMESTAMPTZ) IS NOT NULL
        THEN FALSE
        ELSE TRUE
    END AS brd_awd_dt_invalid,

    brd_awd_no,
    cat_dscr,
    TRY_CAST(doc_vend_ln_no AS INTEGER) AS doc_vend_ln_no,
    vend_cust_cd,
    lgl_nm,
    alias_nm,
    so_doc_cd,
    so_doc_dept_cd,
    so_doc_id,

    TRY_CAST(today AS TIMESTAMPTZ) AS today,
    _ingested_at

FROM bronze_source
ORDER BY row_key
"""


def validate_contracts_source(con) -> None:
    """Reject structural and financial quality failures."""
    result = con.execute(
        """
        SELECT
            COUNT(*) FILTER (
                WHERE row_key IS NULL OR TRIM(row_key) = ''
            ) AS invalid_keys,

            COUNT(*) - COUNT(DISTINCT row_key) AS duplicate_keys,

            COUNT(*) FILTER (
                WHERE ma_prch_lmt_am IS NOT NULL
                  AND TRY_CAST(ma_prch_lmt_am AS DECIMAL(18,2)) IS NULL
            )
            +
            COUNT(*) FILTER (
                WHERE ma_itd_ord_am IS NOT NULL
                  AND TRY_CAST(ma_itd_ord_am AS DECIMAL(18,2)) IS NULL
            )
            +
            COUNT(*) FILTER (
                WHERE ma_do_rfed_am IS NOT NULL
                  AND TRY_CAST(ma_do_rfed_am AS DECIMAL(18,2)) IS NULL
            ) AS invalid_amounts
        FROM bronze_source
        """
    ).fetchone()

    if result is None:
        raise RuntimeError("Contracts source validation returned no result")

    invalid_keys, duplicate_keys, invalid_amounts = result

    if invalid_keys or duplicate_keys or invalid_amounts:
        raise ValueError(
            "Contracts Bronze quality validation failed: "
            f"{invalid_keys} invalid keys, "
            f"{duplicate_keys} duplicate keys, "
            f"{invalid_amounts} invalid amounts"
        )


def transform_contracts_to_silver(con) -> pa.Table:
    """Validate and transform Contracts Bronze records."""
    validate_contracts_source(con)

    records = con.sql(CONTRACTS_SILVER_SQL).to_arrow_table()

    fields = []
    for field in records.schema:
        if pa.types.is_timestamp(field.type) and field.type.tz is not None:
            fields.append(
                field.with_type(
                    pa.timestamp("us", tz="UTC")
                )
            )
        else:
            fields.append(field)

    return records.cast(pa.schema(fields))