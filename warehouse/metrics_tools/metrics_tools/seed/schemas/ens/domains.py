from typing import List, Optional

from metrics_tools.seed.types import Column, SeedConfig
from pydantic import BaseModel


class Resolver(BaseModel):
    id: Optional[str] = Column("VARCHAR")


class Owner(BaseModel):
    id: Optional[str] = Column("VARCHAR")


class Registrant(BaseModel):
    id: Optional[str] = Column("VARCHAR")


class Registration(BaseModel):
    id: Optional[str] = Column("VARCHAR")


class ENSDomains(BaseModel):
    """ENS domains"""

    id: str = Column("VARCHAR", description="Domain ID")
    name: str = Column("VARCHAR", description="Domain name")
    expiry_date: str | None = Column("VARCHAR", description="Expiry date")
    subdomain_count: int | None = Column("INTEGER", description="Subdomain count")
    resolver: Resolver | None = Column("ROW(?)", description="Resolver")
    owner: Owner | None = Column("ROW(?)", description="Owner")
    registrant: Registrant | None = Column("ROW(?)", description="Registrant")
    registration: Registration | None = Column("ROW(?)", description="Registration")
    subdomains: List[str] | None = Column("ARRAY(VARCHAR)", description="Subdomains")


seed = SeedConfig(
    catalog="bigquery",
    schema="ens",
    table="domains_tmp",
    base=ENSDomains,
    rows=[
        ENSDomains(
            id="0x0000000000000000000000000000000000000001",
            name="test.eth",
            resolver=Resolver(id="0xresolver1"),
            owner=Owner(id="0xowner1"),
            registrant=Registrant(id="0xregistrant1"),
            expiry_date="1735689600",
            registration=Registration(id="0xreg1"),
            subdomains=[],
            subdomain_count=0,
        ),
        ENSDomains(
            id="0x0000000000000000000000000000000000000002",
            name="another.eth",
            resolver=Resolver(id="0xresolver2"),
            owner=Owner(id="0xowner2"),
            registrant=Registrant(id="0xregistrant2"),
            expiry_date="1767225600",
            registration=Registration(id="0xreg2"),
            subdomains=[],
            subdomain_count=0,
        ),
    ],
)
