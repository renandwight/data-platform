WITH source AS (
    SELECT *
    FROM read_parquet(
        's3://lakehouse/silver/customers/customers.parquet'
    )
),

renamed AS (
    SELECT
        CAST(id AS INTEGER) AS customer_id,
        CAST(customer_name AS VARCHAR) AS customer_name,
        CAST(created_date AS DATE) AS created_date
    FROM source
)

SELECT *
FROM renamed