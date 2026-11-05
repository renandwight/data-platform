WITH source AS (
    SELECT
        id,
        name,
        name_length
    FROM {{ source('silver', 'integration_test') }}
),

validated AS (
    SELECT
        CAST(id AS INTEGER) AS id,
        CAST(name AS VARCHAR) AS name,
        CAST(name_length AS INTEGER) AS name_length
    FROM source
)

SELECT
    id,
    name,
    name_length
FROM validated