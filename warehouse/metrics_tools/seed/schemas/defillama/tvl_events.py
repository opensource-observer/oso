from datetime import datetime

from metrics_tools.seed.types import Column, SeedConfig
from pydantic import BaseModel


class TvlEvents(BaseModel):
    time: datetime | None = Column("TIMESTAMP")
    slug: str | None = Column("VARCHAR")
    protocol: str | None = Column("VARCHAR")
    parent_protocol: str | None = Column("VARCHAR")
    chain: str | None = Column("VARCHAR")
    token: str | None = Column("VARCHAR")
    tvl: float | None = Column("DOUBLE")
    event_type: str | None = Column("VARCHAR")
    dlt_load_id: str | None = Column("VARCHAR", "_dlt_load_id")
    dlt_id: str | None = Column("VARCHAR", "_dlt_id")


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
