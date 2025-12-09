from datetime import datetime

from metrics_tools.seed.types import Column, SeedConfig
from pydantic import BaseModel


class AllDonations(BaseModel):
    round_num: int | None = Column("INTEGER")
    round_name: str | None = Column("STRING")
    donor_address: str | None = Column("STRING")
    amount_in_usd: float | None = Column("FLOAT")
    recipient_address: str | None = Column("STRING")
    timestamp: datetime | None = Column("TIMESTAMP")
    project_name: str | None = Column("STRING")
    project_id: str | None = Column("STRING")
    round_id: str | None = Column("STRING")
    chain_id: int | None = Column("INTEGER")
    source: str | None = Column("STRING")
    dlt_load_id: str = Column("STRING", column_name="_dlt_load_id")
    dlt_id: str = Column("STRING", column_name="_dlt_id")
    transaction_hash: str | None = Column("STRING")
    donation_id: str | None = Column("STRING")


seed = SeedConfig(
    catalog="bigquery",
    schema="gitcoin",
    table="all_donations",
    base=AllDonations,
    rows=[
        AllDonations(
            round_num=19,
            round_name="1inch LatAm ",
            donor_address="0x47f96d6f38d837e64ac10cad5968bf3b9ba88289",
            amount_in_usd=0.99677568674087524,
            recipient_address="0x1a82d7Ecf0174eF29f03c3bA944607fa91364b7b",
            timestamp=datetime.fromisoformat("2023-11-22 10:06:53.000000+00:00"),
            project_name="Modular Crypto",
            project_id="0x26f68334ab056d605995e73c038faf1e863d8992cd49f6f41091d000d38ba056",
            round_id="0xe168ac27b7c32db85478a6807640c8bca1220d15",
            chain_id=42161,
            source="GrantsStack",
            dlt_load_id="1745498179.209534",
            dlt_id="JqjA7T3ts4v0IQ",
            transaction_hash=None,
            donation_id="b79e3a11aee920f77da79f902b23dac2e5a234bb441dc1479ac71bd4129e45e1",
        ),
        AllDonations(
            round_num=19,
            round_name="1inch LatAm ",
            donor_address="0x45d7d9f4eda19fedd00f8f226bc5ed7462a8a657",
            amount_in_usd=0.6414979100227356,
            recipient_address="0x1a82d7Ecf0174eF29f03c3bA944607fa91364b7b",
            timestamp=datetime.fromisoformat("2023-11-18 12:02:59.000000+00:00"),
            project_name="Modular Crypto",
            project_id="0x26f68334ab056d605995e73c038faf1e863d8992cd49f6f41091d000d38ba056",
            round_id="0xe168ac27b7c32db85478a6807640c8bca1220d15",
            chain_id=42161,
            source="GrantsStack",
            dlt_load_id="1745498179.209534",
            dlt_id="kbwZ1oxaStyJdQ",
            transaction_hash=None,
            donation_id="262dcf3ba63591b61756fbf41b68acb0733f6ce46d617509a7a82e2e26548cfc",
        ),
        AllDonations(
            round_num=19,
            round_name="1inch LatAm ",
            donor_address="0xcb8b30da0a6908b2d36979454a41fa74dcf5a567",
            amount_in_usd=1.3732950687408447,
            recipient_address="0x1a82d7Ecf0174eF29f03c3bA944607fa91364b7b",
            timestamp=datetime.fromisoformat("2023-11-22 07:36:28.000000+00:00"),
            project_name="Modular Crypto",
            project_id="0x26f68334ab056d605995e73c038faf1e863d8992cd49f6f41091d000d38ba056",
            round_id="0xe168ac27b7c32db85478a6807640c8bca1220d15",
            chain_id=42161,
            source="GrantsStack",
            dlt_load_id="1745498179.209534",
            dlt_id="BDZAfDc1RRX0qQ",
            transaction_hash=None,
            donation_id="0f686eb6c1d64e0a77cccd49a29fe21dc584a2839dde1255d11a20a7bf3182bb",
        ),
        AllDonations(
            round_num=19,
            round_name="1inch LatAm ",
            donor_address="0x9afaa8213580e11c8b313e5e12a6b34dcdd303b2",
            amount_in_usd=1.1568416357040405,
            recipient_address="0x1a82d7Ecf0174eF29f03c3bA944607fa91364b7b",
            timestamp=datetime.fromisoformat("2023-11-23 10:50:10.000000+00:00"),
            project_name="Modular Crypto",
            project_id="0x26f68334ab056d605995e73c038faf1e863d8992cd49f6f41091d000d38ba056",
            round_id="0xe168ac27b7c32db85478a6807640c8bca1220d15",
            chain_id=42161,
            source="GrantsStack",
            dlt_load_id="1745498179.209534",
            dlt_id="3/tTkPzErJSnqw",
            transaction_hash=None,
            donation_id="cb801ef0eb5c36960a05ef25906486137b67b0c66f7d8988378ee6f789e5a3e3",
        ),
        AllDonations(
            round_num=19,
            round_name="1inch LatAm ",
            donor_address="0x3e5da3e1f890c94312bc21a443f06eeccbcca9f1",
            amount_in_usd=0.10265535861253738,
            recipient_address="0x1a82d7Ecf0174eF29f03c3bA944607fa91364b7b",
            timestamp=datetime.fromisoformat("2023-11-26 21:50:32.000000+00:00"),
            project_name="Modular Crypto",
            project_id="0x26f68334ab056d605995e73c038faf1e863d8992cd49f6f41091d000d38ba056",
            round_id="0xe168ac27b7c32db85478a6807640c8bca1220d15",
            chain_id=42161,
            source="GrantsStack",
            dlt_load_id="1745498179.209534",
            dlt_id="WcAQmzAnO6Sdpw",
            transaction_hash=None,
            donation_id="fbda4002afb7a76a0486071add770d13ab1d9cff9ac7f98b9c9fd495fb98a70c",
        ),
    ],
)
