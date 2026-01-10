from metrics_tools.seed.types import Column, SeedConfig
from pydantic import BaseModel


class Chains(BaseModel):
    """Stores chain data from DefiLlama"""

    gecko_id: str | None = Column(
        "VARCHAR", description="The CoinGecko ID for the chain"
    )
    tvl: float | None = Column(
        "DOUBLE", description="The total value locked (TVL) in USD"
    )
    token_symbol: str | None = Column(
        "VARCHAR", description="The token symbol for the chain"
    )
    cmc_id: str | None = Column(
        "VARCHAR", description="The CoinMarketCap ID for the chain"
    )
    name: str | None = Column("VARCHAR", description="The name of the chain")
    chain_id: int | None = Column("BIGINT", description="The chain ID")


seed = SeedConfig(
    catalog="bigquery",
    schema="defillama",
    table="chains",
    base=Chains,
    rows=[
        Chains(
            gecko_id="harmony",
            tvl=1438794.7692819044,
            token_symbol="ONE",
            cmc_id="3945",
            name="Harmony",
            chain_id=1666600000,
        ),
        Chains(
            gecko_id="tac",
            tvl=36623730.35917668,
            token_symbol="TAC",
            cmc_id="",
            name="TAC",
            chain_id=239,
        ),
        Chains(
            gecko_id="aurora-near",
            tvl=6403966.311301038,
            token_symbol="AURORA",
            cmc_id="14803",
            name="Aurora",
            chain_id=1313161554,
        ),
        Chains(
            gecko_id="x-layer",
            tvl=5707404.553377907,
            token_symbol="",
            cmc_id="",
            name="X Layer",
            chain_id=None,
        ),
        Chains(
            gecko_id="",
            tvl=9133567.396131674,
            token_symbol="",
            cmc_id="",
            name="Ink",
            chain_id=57073,
        ),
        Chains(
            gecko_id="",
            tvl=26936665.540809367,
            token_symbol="",
            cmc_id="",
            name="Corn",
            chain_id=21000000,
        ),
        Chains(
            gecko_id="celo",
            tvl=53217013.37030759,
            token_symbol="CELO",
            cmc_id="5567",
            name="Celo",
            chain_id=42220,
        ),
    ],
)
