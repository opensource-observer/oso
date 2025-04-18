from datetime import datetime

from metrics_tools.seed.types import Column, SeedConfig
from pydantic import BaseModel


class TvlEvents(BaseModel):
    """Stores TVL values for a given protocol on multiple chains"""

    time: datetime | None = Column("TIMESTAMP", description="The timestamp of the TVL value")
    slug: str | None = Column("VARCHAR", description="The slug of the protocol")
    protocol: str | None = Column("VARCHAR", description="The name of the protocol")
    parent_protocol: str | None = Column("VARCHAR", description="The name of the parent protocol")
    chain: str | None = Column("VARCHAR", description="The name of the chain for the current tvl")
    token: str | None = Column("VARCHAR", description="The token symbol of the TVL value")
    tvl: float | None = Column("DOUBLE", description="The magnitude of the TVL value")
    event_type: str | None = Column("VARCHAR", description="The type of event")
    dlt_load_id: str | None = Column("VARCHAR", column_name="_dlt_load_id", description="Internal only value used by DLT. This is the unix timestamp of the load job that scraped the data")
    dlt_id: str | None = Column("VARCHAR", column_name="_dlt_id", description="Internal only unique value for the row")


seed = SeedConfig(
    catalog="bigquery",
    schema="defillama",
    table="tvl_events",
    base=TvlEvents,
    rows=[
        TvlEvents(
            time=datetime(2024, 11, 8),
            slug="portal",
            protocol="portal",
            parent_protocol="",
            chain="acala",
            token="USD",
            tvl=0.0,
            event_type="TVL",
            dlt_load_id="1743009053.36983",
            dlt_id="yflDrYc0mMETNg",
        ),
        TvlEvents(
            time=datetime(2024, 11, 9),
            slug="portal",
            protocol="portal",
            parent_protocol="",
            chain="acala",
            token="USD",
            tvl=0.0,
            event_type="TVL",
            dlt_load_id="1743009053.36983",
            dlt_id="iy4nV9PKmMGEIg",
        ),
        TvlEvents(
            time=datetime(2024, 11, 6),
            slug="portal",
            protocol="portal",
            parent_protocol="",
            chain="acala",
            token="USD",
            tvl=121.31364,
            event_type="TVL",
            dlt_load_id="1743009053.36983",
            dlt_id="ZiTAxzBJ+qexqQ",
        ),
        TvlEvents(
            time=datetime(2024, 11, 4),
            slug="portal",
            protocol="portal",
            parent_protocol="",
            chain="acala",
            token="USD",
            tvl=120.97663,
            event_type="TVL",
            dlt_load_id="1743009053.36983",
            dlt_id="z7A8190d3UEznw",
        ),
        TvlEvents(
            time=datetime(2024, 11, 3),
            slug="portal",
            protocol="portal",
            parent_protocol="",
            chain="acala",
            token="USD",
            tvl=128.8515,
            event_type="TVL",
            dlt_load_id="1743009053.36983",
            dlt_id="XBuflBJpHMq8bg",
        ),
        TvlEvents(
            time=datetime(2024, 11, 6),
            slug="portal",
            protocol="portal",
            parent_protocol="",
            chain="algorand",
            token="USD",
            tvl=50243.12289,
            event_type="TVL",
            dlt_load_id="1743009053.36983",
            dlt_id="NdZiuWu9l7exQg",
        ),
        TvlEvents(
            time=datetime(2024, 11, 3),
            slug="portal",
            protocol="portal",
            parent_protocol="",
            chain="algorand",
            token="USD",
            tvl=94839.76255,
            event_type="TVL",
            dlt_load_id="1743009053.36983",
            dlt_id="wDtpH0j4O8hQJA",
        ),
        TvlEvents(
            time=datetime(2024, 11, 9),
            slug="portal",
            protocol="portal",
            parent_protocol="",
            chain="algorand",
            token="USD",
            tvl=53368.60227,
            event_type="TVL",
            dlt_load_id="1743009053.36983",
            dlt_id="HE6WvR82yX+ITg",
        ),
    ],
)
