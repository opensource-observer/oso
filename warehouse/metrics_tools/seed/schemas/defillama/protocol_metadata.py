
from metrics_tools.seed.types import Column, SeedConfig
from pydantic import BaseModel


class ProtocolMetadata(BaseModel):
    """Stores metadata about DeFi protocols from DefiLlama"""

    id: str | None = Column("VARCHAR", description="The unique identifier for the protocol")
    slug: str | None = Column("VARCHAR", description="The slug of the protocol")
    name: str | None = Column("VARCHAR", description="The name of the protocol")
    address: str | None = Column("VARCHAR", description="The contract address of the protocol")
    symbol: str | None = Column("VARCHAR", description="The token symbol of the protocol")
    url: str | None = Column("VARCHAR", description="The website URL of the protocol")
    description: str | None = Column("VARCHAR", description="A description of the protocol")
    logo: str | None = Column("VARCHAR", description="URL to the protocol's logo")
    chain: str | None = Column("VARCHAR", description="The primary chain the protocol operates on")
    category: str | None = Column("VARCHAR", description="The category of the protocol")
    twitter: str | None = Column("VARCHAR", description="The Twitter handle of the protocol")
    parent_protocol: str | None = Column("VARCHAR", description="The parent protocol if this is a sub-protocol")
    dlt_load_id: str | None = Column("VARCHAR", column_name="_dlt_load_id", description="Internal value used by DLT indicating when the row was loaded")
    dlt_id: str | None = Column("VARCHAR", column_name="_dlt_id", description="Internal unique value for the row")


seed = SeedConfig(
    catalog="bigquery",
    schema="defillama",
    table="protocol_metadata",
    base=ProtocolMetadata,
    rows=[
        ProtocolMetadata(
            id="359",
            slug="frax",
            name="Frax",
            address="0x3432b6a60d23ca0dfca7761b7ab56459d9c964d0",
            symbol="FXS",
            url="https://frax.finance/",
            description="A dollar-pegged stablecoin using AMO smart contracts and permissionless subprotocols for stability",
            logo="https://icons.llama.fi/frax.jpg",
            chain="Ethereum",
            category="Algo-Stables",
            twitter="fraxfinance",
            parent_protocol="parent#frax-finance",
            dlt_load_id="1750018531.638905",
            dlt_id="mEdZuWrM/p3yFw",
        ),
        ProtocolMetadata(
            id="2607",
            slug="frax-fpi",
            name="Frax FPI",
            address="0xc2544a32872a91f4a553b404c6950e89de901fdb",
            symbol="FPIS",
            url="https://app.frax.finance/fpifpis/fpi",
            description="A stablecoin pegged to a basket of real-world consumer items as defined by the US CPI-U average",
            logo="https://icons.llama.fi/frax-fpi.png",
            chain="Ethereum",
            category="Algo-Stables",
            twitter="fraxfinance",
            parent_protocol="",
            dlt_load_id="1750018531.638905",
            dlt_id="ZN9iFMfRPWCNzA",
        ),
        ProtocolMetadata(
            id="5458",
            slug="pinto",
            name="Pinto",
            address="",
            symbol="-",
            url="https://pinto.money/",
            description="Low volatility money built on Base, forked from the Beanstalk protocol",
            logo="https://icons.llama.fi/pinto.jpg",
            chain="Base",
            category="Algo-Stables",
            twitter="pintodotmoney",
            parent_protocol="",
            dlt_load_id="1750018531.638905",
            dlt_id="2Ob6d0B5IP1vRg",
        ),
        ProtocolMetadata(
            id="504",
            slug="mento",
            name="Mento",
            address="",
            symbol="-",
            url="https://www.mento.org/",
            description="An open source protocol on Celo network facilitating stablecoins like cUSD, cEUR, and cREAL",
            logo="https://icons.llama.fi/mento.png",
            chain="Multi-Chain",
            category="Algo-Stables",
            twitter="MentoLabs",
            parent_protocol="",
            dlt_load_id="1750018531.638905",
            dlt_id="4w5fwPLcl0FZ9Q",
        ),
        ProtocolMetadata(
            id="5567",
            slug="bedrock-brbtc",
            name="Bedrock brBTC",
            address="",
            symbol="-",
            url="https://app.bedrock.technology/brbtc",
            description="A protocol for Bitcoin holders to participate in DeFi, accepting uniBTC and wrapped BTC assets",
            logo="https://icons.llama.fi/bedrock-brbtc.jpg",
            chain="Multi-Chain",
            category="Anchor BTC",
            twitter="Bedrock_DeFi",
            parent_protocol="parent#bedrock",
            dlt_load_id="1750018531.638905",
            dlt_id="KhVGUdvHJOPwRQ",
        ),
    ],
)
