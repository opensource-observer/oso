from metrics_tools.seed.types import Column, SeedConfig
from pydantic import BaseModel


class ENSDomains(BaseModel):
    """ENS domains"""

    id: str = Column("VARCHAR", description="Domain ID")
    name: str = Column("VARCHAR", description="Domain name")
    resolver: str = Column("VARCHAR", description="Resolver JSON")


seed = SeedConfig(
    catalog="bigquery",
    schema="ens",
    table="domains",
    base=ENSDomains,
    rows=[
        ENSDomains(
            id="0x0000000000000000000000000000000000000001",
            name="test.eth",
            resolver='{"id": "0xresolver1"}',
        ),
        ENSDomains(
            id="0x0000000000000000000000000000000000000002",
            name="another.eth",
            resolver='{"id": "0xresolver2"}',
        ),
    ],
)
