WITH source_records AS (
    SELECT row_key
    FROM {{ ref('stg_contracts') }}
),

vendor_lines AS (
    SELECT
        row_key,
        doc_cd,
        doc_dept_cd,
        doc_id
    FROM {{ ref('int_contract_vendor_lines') }}
),

documents AS (
    SELECT
        doc_cd,
        doc_dept_cd,
        doc_id
    FROM {{ ref('int_contract_documents') }}
),

missing_vendor_lines AS (
    SELECT row_key
    FROM source_records

    EXCEPT

    SELECT row_key
    FROM vendor_lines
),

unexpected_vendor_lines AS (
    SELECT row_key
    FROM vendor_lines

    EXCEPT

    SELECT row_key
    FROM source_records
),

orphaned_vendor_lines AS (
    SELECT v.row_key
    FROM vendor_lines AS v
    WHERE NOT EXISTS (
        SELECT 1
        FROM documents AS d
        WHERE v.doc_cd = d.doc_cd
          AND v.doc_dept_cd = d.doc_dept_cd
          AND v.doc_id = d.doc_id
    )
)

SELECT 'missing_vendor_line' AS issue, row_key
FROM missing_vendor_lines

UNION ALL

SELECT 'unexpected_vendor_line' AS issue, row_key
FROM unexpected_vendor_lines

UNION ALL

SELECT 'orphaned_vendor_line' AS issue, row_key
FROM orphaned_vendor_lines