
from metrics_tools.seed.types import Column, SeedConfig
from pydantic import BaseModel


class Chainlist(BaseModel):
    """Stores chain information from Chainlist.org"""

    name: str | None = Column("VARCHAR", description="The name of the chain")
    chain: str | None = Column("VARCHAR", description="The chain identifier")
    chain_id: int | None = Column("INTEGER", description="The chain ID")
    network_id: int | None = Column("INTEGER", description="The network ID")
    short_name: str | None = Column("VARCHAR", description="Short name for the chain")
    chain_slug: str | None = Column("VARCHAR", description="The slug identifier for the chain")
    native_currency_name: str | None = Column("VARCHAR", description="Name of the native currency")
    native_currency_symbol: str | None = Column("VARCHAR", description="Symbol of the native currency")
    native_currency_decimals: int | None = Column("INTEGER", description="Decimals for the native currency")
    info_url: str | None = Column("VARCHAR", description="URL with more information about the chain")


seed = SeedConfig(
    catalog="bigquery",
    schema="chainlist",
    table="chains",
    base=Chainlist,
    rows=[
        Chainlist(
            name="Ethereum Mainnet",
            chain="ETH",
            chain_id=1,
            network_id=1,
            short_name="eth",
            chain_slug="ethereum",
            native_currency_name="Ether",
            native_currency_symbol="ETH",
            native_currency_decimals=18,
            info_url="https://ethereum.org",
        ),
        Chainlist(
            name="Base",
            chain="ETH",
            chain_id=8453,
            network_id=8453,
            short_name="base",
            chain_slug="base",
            native_currency_name="Ether",
            native_currency_symbol="ETH",
            native_currency_decimals=18,
            info_url="https://base.org",
        ),
    ],
)
