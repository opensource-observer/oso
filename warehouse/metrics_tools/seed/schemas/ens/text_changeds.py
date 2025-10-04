from metrics_tools.seed.types import Column, SeedConfig
from pydantic import BaseModel


class ENSTextChangeds(BaseModel):
    """ENS text_changeds"""

    id: str = Column("VARCHAR", description="Text changed event ID")
    resolver: str = Column("VARCHAR", description="Resolver JSON")
    blockNumber: int = Column("INTEGER", description="Block number")
    transactionID: str = Column("VARCHAR", description="Transaction ID")
    key: str = Column("VARCHAR", description="Key")
    value: str = Column("VARCHAR", description="Value")


seed = SeedConfig(
    catalog="bigquery",
    schema="ens",
    table="text_changeds",
    base=ENSTextChangeds,
    rows=[
        ENSTextChangeds(
            id="0x0000000000000000000000000000000000000001",
            resolver='{"id": "0xresolver1"}',
            blockNumber=12345678,
            transactionID="0xtx1",
            key="com.github",
            value="testuser",
        ),
        ENSTextChangeds(
            id="0x0000000000000000000000000000000000000002",
            resolver='{"id": "0xresolver2"}',
            blockNumber=12345679,
            transactionID="0xtx2",
            key="com.github",
            value="anotheruser",
        ),
        ENSTextChangeds(
            id="0x0000000000000000000000000000000000000003",
            resolver='{"id": "0xresolver1"}',
            blockNumber=12345680,
            transactionID="0xtx3",
            key="com.twitter",
            value="testuser",
        ),
    ],
)
