from datetime import datetime

from metrics_tools.seed.types import Column, SeedConfig
from pydantic import BaseModel


class LpFeeEvents(BaseModel):
    """Stores daily LP fee values for a given protocol on each chain"""

    time: datetime | None = Column("TIMESTAMP", description="The timestamp of the LP fee event")
    slug: str | None = Column("VARCHAR", description="The slug of the protocol")
    protocol: str | None = Column("VARCHAR", description="The name of the protocol")
    parent_protocol: str | None = Column("VARCHAR", description="The name of the parent protocol")
    chain: str | None = Column("VARCHAR", description="The name of the chain for the current fee")
    token: str | None = Column("VARCHAR", description="The token symbol of the fee value (typically USD)")
    amount: float | None = Column("DOUBLE", description="The magnitude of the LP fees in USD")
    event_type: str | None = Column("VARCHAR", description="The type of event, always 'LP_FEES' for this seed")
    dlt_load_id: str | None = Column("VARCHAR", column_name="_dlt_load_id", description="Internal value used by DLT indicating when the row was loaded")
    dlt_id: str | None = Column("VARCHAR", column_name="_dlt_id", description="Internal unique value for the row")


seed = SeedConfig(
    catalog="bigquery",
    schema="defillama",
    table="lp_fee_events",
    base=LpFeeEvents,
    rows=[
        LpFeeEvents(
            time=datetime(2024, 11, 1),
            slug="velodrome-v3",
            protocol="velodrome-v3",
            parent_protocol="velodrome",
            chain="optimism",
            token="USD",
            amount=31.0,
            event_type="LP_FEES",
            dlt_load_id="1743009053.36983",
            dlt_id="fee001",
        ),
        LpFeeEvents(
            time=datetime(2024, 11, 2),
            slug="velodrome-v3",
            protocol="velodrome-v3",
            parent_protocol="velodrome",
            chain="optimism",
            token="USD",
            amount=96.0,
            event_type="LP_FEES",
            dlt_load_id="1743009053.36983",
            dlt_id="fee002",
        ),
        LpFeeEvents(
            time=datetime(2024, 11, 3),
            slug="velodrome-v3",
            protocol="velodrome-v3",
            parent_protocol="velodrome",
            chain="optimism",
            token="USD",
            amount=143.0,
            event_type="LP_FEES",
            dlt_load_id="1743009053.36983",
            dlt_id="fee003",
        ),
        LpFeeEvents(
            time=datetime(2024, 11, 4),
            slug="velodrome-v3",
            protocol="velodrome-v3",
            parent_protocol="velodrome",
            chain="optimism",
            token="USD",
            amount=238.0,
            event_type="LP_FEES",
            dlt_load_id="1743009053.36983",
            dlt_id="fee004",
        ),
        LpFeeEvents(
            time=datetime(2024, 11, 5),
            slug="velodrome-v3",
            protocol="velodrome-v3",
            parent_protocol="velodrome",
            chain="optimism",
            token="USD",
            amount=338.0,
            event_type="LP_FEES",
            dlt_load_id="1743009053.36983",
            dlt_id="fee005",
        ),
    ],
)
