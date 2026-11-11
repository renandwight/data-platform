"""Source schema for City of Austin Contracts ingestion."""

from datetime import UTC, datetime

import pyarrow as pa

CONTRACTS_DATASET_ID = "84ih-p28j"
CONTRACTS_TABLE = ("bronze", "contracts")

CONTRACTS_FIELDS = (
    "doc_cd",
    "doc_dept_cd",
    "doc_id",
    "doc_vers_no",
    "doc_dscr",
    "contract_synopsis",
    "contract_contact_nm",
    "contract_contact_voice_ph_no",
    "contract_contact_email_ad",
    "ma_prch_lmt_am",
    "ma_itd_ord_am",
    "ma_do_rfed_am",
    "efbgn_dt",
    "efend_dt",
    "gnrc_po_rpt_1",
    "rpt_dscr",
    "brd_awd_dt",
    "brd_awd_no",
    "cat_dscr",
    "doc_vend_ln_no",
    "vend_cust_cd",
    "lgl_nm",
    "alias_nm",
    "so_doc_cd",
    "so_doc_dept_cd",
    "so_doc_id",
    "today",
    "row_key",
)

CONTRACTS_ARROW_SCHEMA = pa.schema(
    [
        pa.field(
            name,
            pa.string(),
            nullable=name != "row_key",
        )
        for name in CONTRACTS_FIELDS
    ]
    + [
        pa.field(
            "_ingested_at",
            pa.timestamp("us", tz="UTC"),
            nullable=False,
        )
    ]
)


def prepare_contracts(
    records: list[dict],
    ingested_at: datetime | None = None,
) -> pa.Table:
    """Validate Contracts records and prepare a typed Arrow table."""
    if not records:
        raise ValueError("Contracts extraction returned no records")

    keys = [record.get("row_key") for record in records]

    if any(not isinstance(key, str) or not key.strip() for key in keys):
        raise ValueError("Contracts records contain missing or invalid row_key")

    if len(keys) != len(set(keys)):
        raise ValueError("Contracts records contain duplicate row_key values")

    expected_fields = set(CONTRACTS_FIELDS)
    unexpected = set().union(*(record.keys() for record in records)) - expected_fields

    if unexpected:
        raise ValueError(f"Unexpected Contracts fields: {sorted(unexpected)}")

    timestamp = ingested_at or datetime.now(UTC)

    if timestamp.tzinfo is None or timestamp.utcoffset() is None:
        raise ValueError("ingested_at must be timezone-aware")

    normalized = [
        {
            **{
                name: str(record[name]) if record.get(name) is not None else None
                for name in CONTRACTS_FIELDS
            },
            "_ingested_at": timestamp,
        }
        for record in records
    ]

    return pa.Table.from_pylist(normalized, schema=CONTRACTS_ARROW_SCHEMA)