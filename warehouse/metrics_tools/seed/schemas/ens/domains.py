from metrics_tools.seed.types import Column, SeedConfig
from pydantic import BaseModel


class ENSDomains(BaseModel):
    """ENS domains"""

    id: str = Column("VARCHAR", description="Domain ID")
    name: str = Column("VARCHAR", description="Domain name")
    resolver: str = Column("VARCHAR", description="Resolver JSON")
    owner: str | None = Column("VARCHAR", description="Owner JSON")
    registrant: str | None = Column("VARCHAR", description="Registrant JSON")
    expiry_date: str | None = Column("VARCHAR", description="Expiry date")
    registration: str | None = Column("VARCHAR", description="Registration JSON")
    subdomains: str | None = Column("VARCHAR", description="Subdomains JSON")
    subdomain_count: int | None = Column("INTEGER", description="Subdomain count")


seed = SeedConfig(
    catalog="bigquery",
    schema="ens",
    table="domains_tmp",
    base=ENSDomains,
    rows=[
        ENSDomains(
            id="0x0000000000000000000000000000000000000001",
            name="test.eth",
            resolver='{"id": "0xresolver1"}',
            owner='{"id": "0xowner1"}',
            registrant='{"id": "0xregistrant1"}',
            expiry_date="1735689600",
            registration='{"id": "0xreg1"}',
            subdomains="[]",
            subdomain_count=0,
        ),
        ENSDomains(
            id="0x0000000000000000000000000000000000000002",
            name="another.eth",
            resolver='{"id": "0xresolver2"}',
            owner='{"id": "0xowner2"}',
            registrant='{"id": "0xregistrant2"}',
            expiry_date="1767225600",
            registration='{"id": "0xreg2"}',
            subdomains="[]",
            subdomain_count=0,
        ),
    ],
)
