WITH source AS (
    SELECT *
    FROM {{ ref('stg_contracts') }}
),

documents AS (
    SELECT DISTINCT
        doc_cd,
        doc_dept_cd,
        doc_id,
        doc_vers_no,
        doc_dscr,
        contract_synopsis,
        contract_contact_nm,
        contract_contact_voice_ph_no,
        contract_contact_email_ad,
        ma_prch_lmt_am,
        ma_itd_ord_am,
        ma_do_rfed_am,
        efbgn_dt,
        efend_dt,
        gnrc_po_rpt_1,
        rpt_dscr,
        brd_awd_dt_raw,
        brd_awd_dt,
        brd_awd_dt_invalid,
        brd_awd_no,
        cat_dscr,
        so_doc_cd,
        so_doc_dept_cd,
        so_doc_id,
        today,
        _ingested_at
    FROM source
)

SELECT *
FROM documents