from metrics_tools.seed.types import Column, SeedConfig
from pydantic import BaseModel


class ENSTextChangeds(BaseModel):
    """ENS text_changeds"""

    resolver: str = Column("VARCHAR", description="Resolver JSON")
    key: str = Column("VARCHAR", description="Key")
    value: str = Column("VARCHAR", description="Value")


seed = SeedConfig(
    catalog="bigquery",
    schema="ens",
    table="text_changeds",
    base=ENSTextChangeds,
    rows=[
        ENSTextChangeds(
            resolver='{"id": "0xresolver1"}',
            key="com.github",
            value="testuser",
        ),
        ENSTextChangeds(
            resolver='{"id": "0xresolver2"}',
            key="com.github",
            value="anotheruser",
        ),
        ENSTextChangeds(
            resolver='{"id": "0xresolver1"}',
            key="com.twitter",
            value="testuser",
        ),
    ],
)
