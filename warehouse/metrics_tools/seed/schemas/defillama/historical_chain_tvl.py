from datetime import datetime

from metrics_tools.seed.types import Column, SeedConfig
from pydantic import BaseModel


class HistoricalChainTvl(BaseModel):
    """Stores historical TVL values for individual chains from DefiLlama"""

    time: datetime | None = Column(
        "TIMESTAMP", description="The timestamp of the TVL value"
    )
    chain: str | None = Column("VARCHAR", description="The name of the chain")
    tvl: float | None = Column(
        "DOUBLE", description="The magnitude of the TVL value in USD"
    )
    dlt_load_id: str | None = Column(
        "VARCHAR",
        column_name="_dlt_load_id",
        description="Internal only value used by DLT. This is the unix timestamp of the load job that scraped the data",
    )
    dlt_id: str | None = Column(
        "VARCHAR",
        column_name="_dlt_id",
        description="Internal only unique value for the row",
    )


seed = SeedConfig(
    catalog="bigquery",
    schema="defillama",
    table="historical_chain_tvl",
    base=HistoricalChainTvl,
    rows=[
        HistoricalChainTvl(
            time=datetime(2025, 7, 11),
            chain="optimism",
            tvl=408155086.0,
            dlt_load_id="1752201064.6715372",
            dlt_id="0WKqHHJ9MQF61w",
        ),
        HistoricalChainTvl(
            time=datetime(2025, 7, 11),
            chain="ethereum",
            tvl=71986875464.0,
            dlt_load_id="1752201064.6715372",
            dlt_id="DnzlHTQ+Y5EZWQ",
        ),
        HistoricalChainTvl(
            time=datetime(2025, 7, 11),
            chain="arbitrum",
            tvl=2587529382.0,
            dlt_load_id="1752201064.6715372",
            dlt_id="cBImoDJmemAZ7g",
        ),
        HistoricalChainTvl(
            time=datetime(2025, 7, 11),
            chain="base",
            tvl=3772931108.0,
            dlt_load_id="1752201064.6715372",
            dlt_id="dQ+4ZprZsJ4QFw",
        ),
        HistoricalChainTvl(
            time=datetime(2025, 7, 10),
            chain="ethereum",
            tvl=69043173096.0,
            dlt_load_id="1752201064.6715372",
            dlt_id="ggR6tsPfbqh1cg",
        ),
    ],
)
