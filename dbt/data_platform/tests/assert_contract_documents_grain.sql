WITH validation AS (
    SELECT
        COUNT(*) AS total_rows,
        COUNT(DISTINCT (doc_cd, doc_dept_cd, doc_id))
            AS distinct_documents
    FROM {{ ref('int_contract_documents') }}
)

SELECT *
FROM validation
WHERE total_rows <> 341
   OR distinct_documents <> 341