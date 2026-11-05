{{ config(materialized='table') }}

SELECT
    id,
    name,
    name_length
FROM {{ ref('stg_integration_test') }}