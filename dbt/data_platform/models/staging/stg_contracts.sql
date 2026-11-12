WITH source AS (
    SELECT *
    FROM {{ source('silver', 'contracts') }}
),

validated AS (
    SELECT
        CAST(row_key AS VARCHAR) AS row_key,
        CAST(doc_cd AS VARCHAR) AS doc_cd,
        CAST(doc_dept_cd AS VARCHAR) AS doc_dept_cd,
        CAST(doc_id AS VARCHAR) AS doc_id,
        CAST(doc_vers_no AS INTEGER) AS doc_vers_no,
        CAST(doc_dscr AS VARCHAR) AS doc_dscr,
        CAST(contract_synopsis AS VARCHAR) AS contract_synopsis,
        CAST(contract_contact_nm AS VARCHAR) AS contract_contact_nm,
        CAST(contract_contact_voice_ph_no AS VARCHAR) AS contract_contact_voice_ph_no,
        CAST(contract_contact_email_ad AS VARCHAR) AS contract_contact_email_ad,

        CAST(ma_prch_lmt_am AS DECIMAL(18,2)) AS ma_prch_lmt_am,
        CAST(ma_itd_ord_am AS DECIMAL(18,2)) AS ma_itd_ord_am,
        CAST(ma_do_rfed_am AS DECIMAL(18,2)) AS ma_do_rfed_am,

        CAST(efbgn_dt AS TIMESTAMPTZ) AS efbgn_dt,
        CAST(efend_dt AS TIMESTAMPTZ) AS efend_dt,

        CAST(gnrc_po_rpt_1 AS VARCHAR) AS gnrc_po_rpt_1,
        CAST(rpt_dscr AS VARCHAR) AS rpt_dscr,
        CAST(brd_awd_dt_raw AS VARCHAR) AS brd_awd_dt_raw,
        CAST(brd_awd_dt AS TIMESTAMPTZ) AS brd_awd_dt,
        CAST(brd_awd_dt_invalid AS BOOLEAN) AS brd_awd_dt_invalid,

        CAST(brd_awd_no AS VARCHAR) AS brd_awd_no,
        CAST(cat_dscr AS VARCHAR) AS cat_dscr,
        CAST(doc_vend_ln_no AS INTEGER) AS doc_vend_ln_no,
        CAST(vend_cust_cd AS VARCHAR) AS vend_cust_cd,
        CAST(lgl_nm AS VARCHAR) AS lgl_nm,
        CAST(alias_nm AS VARCHAR) AS alias_nm,
        CAST(so_doc_cd AS VARCHAR) AS so_doc_cd,
        CAST(so_doc_dept_cd AS VARCHAR) AS so_doc_dept_cd,
        CAST(so_doc_id AS VARCHAR) AS so_doc_id,
        CAST(today AS TIMESTAMPTZ) AS today,
        CAST(_ingested_at AS TIMESTAMPTZ) AS _ingested_at
    FROM source
)

SELECT *
FROM validated