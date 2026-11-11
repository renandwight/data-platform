"""Unit tests for Contracts ingestion preparation."""

from datetime import UTC, datetime

import pytest

from data_platform.ingestion.contracts import prepare_contracts


def test_prepare_contracts_success():
    timestamp = datetime(2026, 11, 11, tzinfo=UTC)

    table = prepare_contracts(
        [
            {"row_key": "contract-1", "doc_id": "123"},
            {"row_key": "contract-2", "doc_id": "456"},
        ],
        ingested_at=timestamp,
    )

    assert table.num_rows == 2
    assert table.num_columns == 29
    assert table.column("row_key").to_pylist() == [
        "contract-1",
        "contract-2",
    ]
    assert table.column("contract_synopsis").null_count == 2
    assert table.column("_ingested_at").to_pylist() == [
        timestamp,
        timestamp,
    ]


@pytest.mark.parametrize(
    "records",
    [
        [],
        [{"doc_id": "123"}],
        [{"row_key": ""}],
        [{"row_key": "duplicate"}, {"row_key": "duplicate"}],
    ],
)
def test_prepare_contracts_invalid_records(records):
    with pytest.raises(ValueError):
        prepare_contracts(records)


def test_prepare_contracts_unexpected_field():
    with pytest.raises(ValueError, match="Unexpected Contracts fields"):
        prepare_contracts(
            [{"row_key": "contract-1", "unknown_field": "value"}]
        )


def test_prepare_contracts_naive_timestamp():
    with pytest.raises(ValueError, match="timezone-aware"):
        prepare_contracts(
            [{"row_key": "contract-1"}],
            ingested_at=datetime(2026, 11, 11),  # noqa: DTZ001
        )