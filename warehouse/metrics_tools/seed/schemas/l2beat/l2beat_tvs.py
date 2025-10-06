from datetime import datetime

from metrics_tools.seed.types import Column, SeedConfig
from pydantic import BaseModel


class L2beatTvs(BaseModel):
    """Stores L2beat Total Value Secured (TVS) data for various blockchain projects"""

    project_slug: str | None = Column(
        "VARCHAR", description="The slug identifier for the blockchain project"
    )
    timestamp: int | None = Column(
        "INTEGER", description="Unix timestamp of the data point"
    )
    native: int | None = Column("BIGINT", description="Native token value secured")
    canonical: int | None = Column(
        "BIGINT", description="Canonical token value secured"
    )
    external: int | None = Column("BIGINT", description="External token value secured")
    eth_price: float | None = Column("FLOAT", description="ETH price at the time")
    canonical__v_double: float | None = Column(
        "DOUBLE", description="Canonical value as double"
    )
    external__v_double: float | None = Column(
        "DOUBLE", description="External value as double"
    )
    native__v_double: float | None = Column(
        "DOUBLE", description="Native value as double"
    )


seed = SeedConfig(
    catalog="bigquery",
    schema="l2beat",
    table="tvs",
    base=L2beatTvs,
    rows=[
        L2beatTvs(
            project_slug="base",
            timestamp=int(datetime.now().timestamp()),
            native=5369497088,
            canonical=4251012352,
            external=5025510912,
            eth_price=4352.6973,
            canonical__v_double=None,
            external__v_double=None,
            native__v_double=None,
        ),
        L2beatTvs(
            project_slug="katana",
            timestamp=int(datetime.now().timestamp()),
            native=5096511,
            canonical=226320688,
            external=242770768,
            eth_price=4352.6973,
            canonical__v_double=None,
            external__v_double=None,
            native__v_double=None,
        ),
        L2beatTvs(
            project_slug="arbitrum",
            timestamp=int(datetime.now().timestamp()),
            native=3639896832,
            canonical=5670418944,
            external=9844511744,
            eth_price=4352.6973,
            canonical__v_double=None,
            external__v_double=None,
            native__v_double=None,
        ),
        L2beatTvs(
            project_slug="unichain",
            timestamp=int(datetime.now().timestamp()),
            native=0,
            canonical=348103232,
            external=507757856,
            eth_price=4352.6973,
            canonical__v_double=None,
            external__v_double=None,
            native__v_double=None,
        ),
        L2beatTvs(
            project_slug="mantle",
            timestamp=int(datetime.now().timestamp()),
            native=30293092,
            canonical=1521966464,
            external=520220896,
            eth_price=4352.6973,
            canonical__v_double=None,
            external__v_double=None,
            native__v_double=None,
        ),
        L2beatTvs(
            project_slug="blast",
            timestamp=int(datetime.now().timestamp()),
            native=110077664,
            canonical=None,
            external=219649248,
            eth_price=4352.6973,
            canonical__v_double=1271696.25,
            external__v_double=None,
            native__v_double=None,
        ),
        L2beatTvs(
            project_slug="hpp",
            timestamp=int(datetime.now().timestamp()),
            native=None,
            canonical=None,
            external=None,
            eth_price=None,
            canonical__v_double=None,
            external__v_double=None,
            native__v_double=None,
        ),
        L2beatTvs(
            project_slug="silentdata",
            timestamp=int(datetime.now().timestamp()),
            native=None,
            canonical=None,
            external=None,
            eth_price=None,
            canonical__v_double=None,
            external__v_double=None,
            native__v_double=None,
        ),
        L2beatTvs(
            project_slug="reddiozkvm",
            timestamp=int(datetime.now().timestamp()),
            native=None,
            canonical=None,
            external=None,
            eth_price=None,
            canonical__v_double=None,
            external__v_double=None,
            native__v_double=None,
        ),
        L2beatTvs(
            project_slug="intmax",
            timestamp=int(datetime.now().timestamp()),
            native=None,
            canonical=None,
            external=None,
            eth_price=None,
            canonical__v_double=None,
            external__v_double=None,
            native__v_double=None,
        ),
    ],
)
