from metrics_tools.seed.types import Column, SeedConfig
from pydantic import BaseModel


class FundamentalsFull(BaseModel):
    """Stores fundamental metrics for different origins (chains/protocols) from GrowThePie"""

    metric_key: str | None = Column(
        "VARCHAR",
        description="The type of metric being measured (e.g., market_cap_eth, market_cap_usd)",
    )
    origin_key: str | None = Column(
        "VARCHAR",
        description="The origin/chain/protocol identifier (e.g., arbitrum, blast, celo)",
    )
    date: str | None = Column("DATE", description="The date of the metric measurement")
    value: float | None = Column(
        "DOUBLE", description="The numerical value of the metric"
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
    schema="growthepie",
    table="fundamentals_full",
    base=FundamentalsFull,
    rows=[
        FundamentalsFull(
            metric_key="market_cap_eth",
            origin_key="arbitrum",
            date="2025-07-16",
            value=691769.0,
            dlt_load_id="1752677526.5693965",
            dlt_id="IoYNEfn2Mk6PpQ",
        ),
        FundamentalsFull(
            metric_key="market_cap_usd",
            origin_key="arbitrum",
            date="2025-07-16",
            value=2167519917.0,
            dlt_load_id="1752677526.5693965",
            dlt_id="BLt6ixEvKywcYw",
        ),
        FundamentalsFull(
            metric_key="market_cap_usd",
            origin_key="blast",
            date="2025-07-16",
            value=103515518.0,
            dlt_load_id="1752677526.5693965",
            dlt_id="VK84n8uzGKD6UA",
        ),
        FundamentalsFull(
            metric_key="market_cap_eth",
            origin_key="blast",
            date="2025-07-16",
            value=33036.0,
            dlt_load_id="1752677526.5693965",
            dlt_id="7fDViS4NOfS0Cw",
        ),
        FundamentalsFull(
            metric_key="market_cap_eth",
            origin_key="celo",
            date="2025-07-16",
            value=63023.0,
            dlt_load_id="1752677526.5693965",
            dlt_id="HKXb3B/7uY5Mvg",
        ),
    ],
)
