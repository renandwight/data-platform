"""Unit tests for Contracts Bronze-to-Silver transformations."""

import duckdb
import pytest

from data_platform.transformations.contracts import (
    transform_contracts_to_silver,
)


@pytest.fixture
def con():
    """Create an isolated DuckDB connection with sample Bronze data."""
    connection = duckdb.connect(":memory:")

    connection.execute(
        """
        CREATE TABLE bronze_source (
            row_key VARCHAR,
            doc_cd VARCHAR,
            doc_dept_cd VARCHAR,
            doc_id VARCHAR,
            doc_vers_no VARCHAR,
            doc_dscr VARCHAR,
            contract_synopsis VARCHAR,
            contract_contact_nm VARCHAR,
            contract_contact_voice_ph_no VARCHAR,
            contract_contact_email_ad VARCHAR,
            ma_prch_lmt_am VARCHAR,
            ma_itd_ord_am VARCHAR,
            ma_do_rfed_am VARCHAR,
            efbgn_dt VARCHAR,
            efend_dt VARCHAR,
            gnrc_po_rpt_1 VARCHAR,
            rpt_dscr VARCHAR,
            brd_awd_dt VARCHAR,
            brd_awd_no VARCHAR,
            cat_dscr VARCHAR,
            doc_vend_ln_no VARCHAR,
            vend_cust_cd VARCHAR,
            lgl_nm VARCHAR,
            alias_nm VARCHAR,
            so_doc_cd VARCHAR,
            so_doc_dept_cd VARCHAR,
            so_doc_id VARCHAR,
            today VARCHAR,
            _ingested_at TIMESTAMPTZ
        )
        """
    )

    yield connection
    connection.close()


def insert_contract(con, row_key, **overrides):
    """Insert a minimal Contracts record with optional field overrides."""
    values = {
        "row_key": row_key,
        "doc_id": "12345",
        "doc_vers_no": "1",
        "doc_vend_ln_no": "1",
        "ma_prch_lmt_am": "100000.50",
        "ma_itd_ord_am": "75000.25",
        "ma_do_rfed_am": "50000.00",
        "efbgn_dt": "2023-01-01T00:00:00.000Z",
        "efend_dt": "2025-12-31T00:00:00.000Z",
        "brd_awd_dt": "0023-03-04T00:00:00.000Z",
        "today": "2026-11-09T00:00:00.000Z",
    }
    values.update(overrides)

    columns = ", ".join(values)
    placeholders = ", ".join("?" for _ in values)

    con.execute(
        f"INSERT INTO bronze_source ({columns}) VALUES ({placeholders})",
        list(values.values()),
    )


def test_financial_conversion(con):
    insert_contract(con, "contract-1")

    table = transform_contracts_to_silver(con)

    assert table.num_rows == 1
    assert str(table.column("ma_prch_lmt_am")[0].as_py()) == "100000.50"
    assert str(table.column("ma_itd_ord_am")[0].as_py()) == "75000.25"
    assert str(table.column("ma_do_rfed_am")[0].as_py()) == "50000.00"


def test_invalid_award_date_preserved_and_flagged(con):
    insert_contract(con, "contract-1")

    table = transform_contracts_to_silver(con)

    assert table.column("brd_awd_dt_raw")[0].as_py() == (
        "0023-03-04T00:00:00.000Z"
    )
    assert table.column("brd_awd_dt")[0].as_py() is None
    assert table.column("brd_awd_dt_invalid")[0].as_py() is True


def test_missing_optional_dates(con):
    insert_contract(
        con,
        "contract-1",
        efend_dt=None,
        brd_awd_dt=None,
    )

    table = transform_contracts_to_silver(con)

    assert table.column("efend_dt")[0].as_py() is None
    assert table.column("brd_awd_dt")[0].as_py() is None
    assert table.column("brd_awd_dt_invalid")[0].as_py() is False


def test_valid_award_date(con):
    insert_contract(
        con,
        "contract-1",
        brd_awd_dt="2023-03-04T00:00:00.000Z",
    )

    table = transform_contracts_to_silver(con)

    assert table.column("brd_awd_dt")[0].as_py() is not None
    assert table.column("brd_awd_dt_invalid")[0].as_py() is False


def test_duplicate_keys_rejected(con):
    insert_contract(con, "duplicate")
    insert_contract(con, "duplicate")

    with pytest.raises(ValueError, match="duplicate keys"):
        transform_contracts_to_silver(con)


def test_invalid_financial_amount_rejected(con):
    insert_contract(
        con,
        "contract-1",
        ma_prch_lmt_am="not-a-number",
    )

    with pytest.raises(ValueError, match="invalid amounts"):
        transform_contracts_to_silver(con)


def test_missing_key_rejected(con):
    insert_contract(con, None)

    with pytest.raises(ValueError, match="invalid keys"):
        transform_contracts_to_silver(con)


def test_timestamps_normalized_to_utc(con):
    """Silver timestamps must use UTC for Iceberg compatibility."""
    insert_contract(con, "contract-1")

    table = transform_contracts_to_silver(con)

    timestamp_columns = [
        "efbgn_dt",
        "efend_dt",
        "brd_awd_dt",
        "today",
        "_ingested_at",
    ]

    for column in timestamp_columns:
        assert table.schema.field(column).type.tz == "UTC"