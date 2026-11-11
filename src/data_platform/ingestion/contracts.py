"""Source schema for City of Austin Contracts ingestion."""

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
