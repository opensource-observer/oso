from datetime import datetime, timedelta

from metrics_tools.seed.types import Column, SeedConfig
from pydantic import BaseModel


class Raises(BaseModel):
    """Stores fundraising data from DefiLlama"""

    date: datetime = Column(
        "TIMESTAMP", description="The date of the fundraising event"
    )
    name: str = Column("VARCHAR", description="The name of the protocol")
    round: str = Column("VARCHAR", description="The fundraising round")
    amount: float = Column("DOUBLE", description="The amount raised in USD")
    chains: list[str] = Column("JSON", description="Chains the protocol is on")
    sector: str = Column("VARCHAR", description="The sector of the protocol")
    category: str = Column("VARCHAR", description="The category of the protocol")
    category_group: str = Column(
        "VARCHAR", description="The category group of the protocol"
    )
    source: str = Column("VARCHAR", description="The source of the information")
    lead_investors: list[str] = Column(
        "JSON", description="Lead investors in the round"
    )
    other_investors: list[str] = Column(
        "JSON", description="Other investors in the round"
    )
    defillama_id: str = Column(
        "VARCHAR", description="The DefiLlama ID for the protocol"
    )
    valuation: float = Column(
        "DOUBLE", description="The valuation of the protocol in USD"
    )
    dlt_load_id: str = Column(
        "VARCHAR",
        column_name="_dlt_load_id",
        description="Internal only value used by DLT. This is the unix timestamp of the load job that scraped the data",
    )
    dlt_id: str = Column(
        "VARCHAR",
        column_name="_dlt_id",
        description="Internal only unique value for the row",
    )


seed = SeedConfig(
    catalog="bigquery",
    schema="defillama",
    table="raises",
    base=Raises,
    rows=[
        Raises(
            date=datetime.now() - timedelta(days=2),
            name="EigenLayer",
            round="Series B",
            amount=100000000.0,
            chains=["Ethereum"],
            sector="Restaking",
            category="Protocol",
            category_group="DeFi",
            source="a16zcrypto",
            lead_investors=["a16zcrypto"],
            other_investors=["Coinbase Ventures", "Polychain Capital"],
            defillama_id="3783",
            valuation=1000000000.0,
            dlt_load_id="1743009053.36983",
            dlt_id="raise001",
        ),
        Raises(
            date=datetime.now() - timedelta(days=1),
            name="Puffer Finance",
            round="Seed",
            amount=18000000.0,
            chains=["Ethereum"],
            sector="Liquid Restaking",
            category="Protocol",
            category_group="DeFi",
            source="Binance Labs",
            lead_investors=["Binance Labs", "Electric Capital"],
            other_investors=["Animoca Brands"],
            defillama_id="5343",
            valuation=200000000.0,
            dlt_load_id="1743009053.36983",
            dlt_id="raise002",
        ),
        Raises(
            date=datetime.now(),
            name="Farcaster",
            round="Series A",
            amount=150000000.0,
            chains=["Ethereum", "Optimism"],
            sector="Social",
            category="dApp",
            category_group="Social",
            source="Paradigm",
            lead_investors=["Paradigm"],
            other_investors=["a16zcrypto", "USV", "Variant"],
            defillama_id="42",
            valuation=1000000000.0,
            dlt_load_id="1743009053.36983",
            dlt_id="raise003",
        ),
    ],
)
