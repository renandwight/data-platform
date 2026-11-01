
"""Reusable Bronze-to-Silver transformation definitions."""

BRONZE_TO_SILVER_SQL = """
SELECT
    id,
    UPPER(TRIM(name)) AS name,
    CAST(LENGTH(TRIM(name)) AS INTEGER) AS name_length
FROM bronze_source
ORDER BY id
"""


def validate_source(con) -> None:
    """Reject null, blank, or duplicate source records."""

    invalid_count = con.execute(
        """
        SELECT COUNT(*)
        FROM bronze_source
        WHERE id IS NULL
           OR name IS NULL
           OR TRIM(name) = ''
        """
    ).fetchone()[0]

    duplicate_count = con.execute(
        """
        SELECT COUNT(*)
        FROM (
            SELECT id
            FROM bronze_source
            GROUP BY id
            HAVING COUNT(*) > 1
        )
        """
    ).fetchone()[0]

    if invalid_count or duplicate_count:
        raise ValueError(
            "Bronze quality validation failed: "
            f"{invalid_count} invalid records, "
            f"{duplicate_count} duplicate IDs"
        )


def transform_bronze_to_silver(con):
    """Validate and transform the registered Bronze source."""

    validate_source(con)

    return con.execute(
        BRONZE_TO_SILVER_SQL
    ).fetchall()
