WITH customers AS (
    SELECT
        customer_id,
        customer_name,
        created_date
    FROM {{ ref('stg_customers') }}
)

SELECT
    customer_id,
    customer_name,
    created_date
FROM customers