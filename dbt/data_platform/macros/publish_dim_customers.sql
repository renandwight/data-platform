{% macro publish_dim_customers() %}

    {% do run_query("CREATE TABLE IF NOT EXISTS pg.gold.dim_customers (customer_id INTEGER PRIMARY KEY, customer_name VARCHAR, created_date DATE)") %}

    {% do run_query("DELETE FROM pg.gold.dim_customers") %}

    {% do run_query("
        INSERT INTO pg.gold.dim_customers
        SELECT
            customer_id,
            customer_name,
            created_date
        FROM main.dim_customers
    ") %}

{% endmacro %}