from typing import Optional

from metrics_tools.seed.types import Column, SeedConfig
from pydantic import BaseModel


class Resolver(BaseModel):
    id: Optional[str] = Column("VARCHAR")


class ENSTextChangeds(BaseModel):
    """ENS text_changeds"""

    id: str = Column("VARCHAR", description="Text changed event ID")
    block_number: int = Column("INTEGER", description="Block number")
    transaction_id: str = Column("VARCHAR", description="Transaction ID")
    key: str = Column("VARCHAR", description="Key")
    value: str = Column("VARCHAR", description="Value")
    resolver: Resolver | None = Column("ROW(?)", description="Resolver")


seed = SeedConfig(
    catalog="bigquery",
    schema="ens",
    table="text_changeds",
    base=ENSTextChangeds,
    rows=[
        ENSTextChangeds(
            id="0x0000000000000000000000000000000000000001",
            resolver=Resolver(id="0xresolver1"),
            block_number=12345678,
            transaction_id="0xtx1",
            key="com.github",
            value="testuser",
        ),
        ENSTextChangeds(
            id="0x0000000000000000000000000000000000000002",
            resolver=Resolver(id="0xresolver2"),
            block_number=12345679,
            transaction_id="0xtx2",
            key="com.github",
            value="anotheruser",
        ),
        ENSTextChangeds(
            id="0x0000000000000000000000000000000000000003",
            resolver=Resolver(id="0xresolver1"),
            block_number=12345680,
            transaction_id="0xtx3",
            key="com.twitter",
            value="testuser",
        ),
    ],
)
