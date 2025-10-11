from metrics_tools.seed.types import Column, SeedConfig
from pydantic import BaseModel


class ENSTextChangeds(BaseModel):
    """ENS text_changeds"""

    id: str = Column("VARCHAR", description="Text changed event ID")
    resolver: str = Column("VARCHAR", description="Resolver JSON")
    block_number: int = Column("INTEGER", description="Block number")
    transaction_id: str = Column("VARCHAR", description="Transaction ID")
    text_changed_key: str = Column("VARCHAR", description="Key")
    text_changed_value: str = Column("VARCHAR", description="Value")


seed = SeedConfig(
    catalog="bigquery",
    schema="ens",
    table="text_changeds",
    base=ENSTextChangeds,
    rows=[
        ENSTextChangeds(
            id="0x0000000000000000000000000000000000000001",
            resolver='{"id": "0xresolver1"}',
            block_number=12345678,
            transaction_id="0xtx1",
            text_changed_key="com.github",
            text_changed_value="testuser",
        ),
        ENSTextChangeds(
            id="0x0000000000000000000000000000000000000002",
            resolver='{"id": "0xresolver2"}',
            block_number=12345679,
            transaction_id="0xtx2",
            text_changed_key="com.github",
            text_changed_value="anotheruser",
        ),
        ENSTextChangeds(
            id="0x0000000000000000000000000000000000000003",
            resolver='{"id": "0xresolver1"}',
            block_number=12345680,
            transaction_id="0xtx3",
            text_changed_key="com.twitter",
            text_changed_value="testuser",
        ),
    ],
)
