WITH source AS (
    SELECT
        row_key,
        doc_cd,
        doc_dept_cd,
        doc_id,
        doc_vers_no,
        doc_vend_ln_no,
        vend_cust_cd,
        lgl_nm,
        alias_nm
    FROM {{ ref('stg_contracts') }}
)

SELECT
    row_key,
    doc_cd,
    doc_dept_cd,
    doc_id,
    doc_vers_no,
    doc_vend_ln_no,
    vend_cust_cd,
    lgl_nm,
    alias_nm
FROM source