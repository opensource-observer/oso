from datetime import datetime

from metrics_tools.seed.types import Column, SeedConfig
from pydantic import BaseModel


class AllMatching(BaseModel):
    matching_id: str | None = Column("STRING")
    round_num: int | None = Column("INTEGER")
    title: str | None = Column("STRING")
    match_amount_in_usd: float | None = Column("FLOAT")
    recipient_address: str | None = Column("STRING")
    project_id: str | None = Column("STRING")
    round_id: str | None = Column("STRING")
    chain_id: int | None = Column("INTEGER")
    dlt_load_id: str = Column("STRING", column_name="_dlt_load_id")
    dlt_id: str = Column("STRING", column_name="_dlt_id")
    timestamp: datetime | None = Column("TIMESTAMP")


seed = SeedConfig(
    catalog="bigquery",
    schema="gitcoin",
    table="all_matching",
    base=AllMatching,
    rows=[
        AllMatching(
            matching_id="18565b4ff46b4ca1c995d616594fd7148962a88cd878f50f48ce559bf20fe2f8",
            round_num=18,
            title="Candide Labs",
            match_amount_in_usd=3302.6202202187496,
            recipient_address="0xc52fbf3769056ca421656b9c98b14a453a251a28",
            project_id="0x6ebed815eef2ae11dd17e86ec396d6c081f5271f1a5163b85ce804e70bc4860e",
            round_id="0x222ea76664ed77d18d4416d2b2e77937b76f0a35",
            chain_id=424,
            dlt_load_id="1745496936.4076033",
            dlt_id="UI51DxvIMJkBsg",
            timestamp=None,
        ),
        AllMatching(
            matching_id="1d7fcf6dce9ad81c00dd54065027b3ae77aa1d34cc8fc6016c84baa514477647",
            round_num=18,
            title="Stereum - Ethereum Node Installer & Manager",
            match_amount_in_usd=1168.83916628125,
            recipient_address="0x6e41fe2f8303b89c9dbccabe59a7f7f8f4312ca9",
            project_id="0xaa09ef03fe5e4d9a0aa3d49a203ea8d1d89969e19cfe8af2135ecec38f035ae0",
            round_id="0x222ea76664ed77d18d4416d2b2e77937b76f0a35",
            chain_id=424,
            dlt_load_id="1745496936.4076033",
            dlt_id="obuBAJHANQPKaw",
            timestamp=None,
        ),
        AllMatching(
            matching_id="255f36ff427dbd11a377614de3b4fd1a061bba36608be3d2400bedb1f8589fac",
            round_num=18,
            title="Ethereum Attestation Service",
            match_amount_in_usd=8089.4460201562506,
            recipient_address="0xcabf67f2c6ef266d68e4206d0a78e035121730bd",
            project_id="0xcedfb9ec17d6bb6a62026f04cd86b71ff3c5b0985fbfd501a27f78676402ab8e",
            round_id="0x222ea76664ed77d18d4416d2b2e77937b76f0a35",
            chain_id=424,
            dlt_load_id="1745496936.4076033",
            dlt_id="Q/mRxFvaGYJjbQ",
            timestamp=None,
        ),
        AllMatching(
            matching_id="230960a088f1337404412513f8e10989e2ace32aa26459b0f756fc020cd678c2",
            round_num=18,
            title="eth.limo",
            match_amount_in_usd=14286.49521603125,
            recipient_address="0xb352bb4e2a4f27683435f153a259f1b207218b1b",
            project_id="0xa7421049dfb7dcacaa3c423aaa31fbfeae4e091825a8c937423a7e3b3fd79888",
            round_id="0x222ea76664ed77d18d4416d2b2e77937b76f0a35",
            chain_id=424,
            dlt_load_id="1745496936.4076033",
            dlt_id="ubKwwivABnbk4w",
            timestamp=None,
        ),
        AllMatching(
            matching_id="f8047617202c9f6636f0c146c19c714892d5ea3604b0de55848c5c9e34ec3f40",
            round_num=18,
            title="ethers.js",
            match_amount_in_usd=6809.33606271875,
            recipient_address="0x8ba1f109551bd432803012645ac136ddd64dba72",
            project_id="0xe0acd0898fada5b0a3f1a6a918858f39fdb7f8408f62a0f583afb70fe488022b",
            round_id="0x222ea76664ed77d18d4416d2b2e77937b76f0a35",
            chain_id=424,
            dlt_load_id="1745496936.4076033",
            dlt_id="1OTHV3J19HWV7Q",
            timestamp=None,
        ),
    ],
)
