{% macro configure_minio() %}
    {% set sql %}
        CREATE OR REPLACE TEMPORARY SECRET minio_secret (
            TYPE s3,
            PROVIDER credential_chain,
            CHAIN 'env',
            REGION 'us-east-1',
            ENDPOINT 'localhost:9000',
            USE_SSL false,
            URL_STYLE 'path',
            SCOPE 's3://lakehouse'
        );
    {% endset %}

    {% do run_query(sql) %}
{% endmacro %}