from datetime import datetime

from metrics_tools.seed.types import Column, SeedConfig
from pydantic import BaseModel


class TradingVolumeEvents(BaseModel):
    """Stores daily trading volume values for a given protocol on each chain"""

    time: datetime | None = Column("TIMESTAMP", description="The timestamp of the volume event")
    slug: str | None = Column("VARCHAR", description="The slug of the protocol")
    protocol: str | None = Column("VARCHAR", description="The name of the protocol")
    parent_protocol: str | None = Column("VARCHAR", description="The name of the parent protocol")
    chain: str | None = Column("VARCHAR", description="The name of the chain for the current volume")
    token: str | None = Column("VARCHAR", description="The token symbol of the volume value (typically USD)")
    volume_usd: float | None = Column("DOUBLE", description="The magnitude of the trading volume in USD")
    event_type: str | None = Column("VARCHAR", description="The type of event, always 'TRADING_VOLUME' for this seed")
    dlt_load_id: str | None = Column("VARCHAR", column_name="_dlt_load_id", description="Internal value used by DLT indicating when the row was loaded")
    dlt_id: str | None = Column("VARCHAR", column_name="_dlt_id", description="Internal unique value for the row")


seed = SeedConfig(
    catalog="bigquery",
    schema="defillama",
    table="trading_volume_events",
    base=TradingVolumeEvents,
    rows=[
        TradingVolumeEvents(
            time=datetime(2024, 11, 1),
            slug="velodrome-v1",
            protocol="velodrome-v1",
            parent_protocol="velodrome",
            chain="optimism",
            token="USD",
            volume_usd=20447576.0,
            event_type="TRADING_VOLUME",
            dlt_load_id="1743009053.36983",
            dlt_id="vol001",
        ),
        TradingVolumeEvents(
            time=datetime(2024, 11, 2),
            slug="velodrome-v1",
            protocol="velodrome-v1",
            parent_protocol="velodrome",
            chain="optimism",
            token="USD",
            volume_usd=17609817.0,
            event_type="TRADING_VOLUME",
            dlt_load_id="1743009053.36983",
            dlt_id="vol002",
        ),
        TradingVolumeEvents(
            time=datetime(2024, 11, 3),
            slug="velodrome-v1",
            protocol="velodrome-v1",
            parent_protocol="velodrome",
            chain="optimism",
            token="USD",
            volume_usd=6649231.0,
            event_type="TRADING_VOLUME",
            dlt_load_id="1743009053.36983",
            dlt_id="vol003",
        ),
        TradingVolumeEvents(
            time=datetime(2024, 11, 4),
            slug="velodrome-v1",
            protocol="velodrome-v1",
            parent_protocol="velodrome",
            chain="optimism",
            token="USD",
            volume_usd=9976414.0,
            event_type="TRADING_VOLUME",
            dlt_load_id="1743009053.36983",
            dlt_id="vol004",
        ),
        TradingVolumeEvents(
            time=datetime(2024, 11, 5),
            slug="velodrome-v1",
            protocol="velodrome-v1",
            parent_protocol="velodrome",
            chain="optimism",
            token="USD",
            volume_usd=12023455.0,
            event_type="TRADING_VOLUME",
            dlt_load_id="1743009053.36983",
            dlt_id="vol005",
        ),
    ],
)
