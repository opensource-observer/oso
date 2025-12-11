from datetime import datetime

from metrics_tools.seed.types import Column, SeedConfig
from pydantic import BaseModel


class EcosystemsChildEcosystems(BaseModel):
    """Seed model for opendevdata ecosystems_child_ecosystems"""

    id: int | None = Column("BIGINT", description="id")
    created_at: datetime | None = Column("TIMESTAMP", description="created at")
    parent_id: int | None = Column("BIGINT", description="parent id")
    child_id: int | None = Column("BIGINT", description="child id")
    connected_at: datetime | None = Column("TIMESTAMP", description="connected at")


seed = SeedConfig(
    catalog="bigquery",
    schema="opendevdata",
    table="ecosystems_child_ecosystems",
    base=EcosystemsChildEcosystems,
    rows=[
        EcosystemsChildEcosystems(
            id=593146,
            created_at=datetime.fromisoformat("2024-10-22 16:09:56"),
            parent_id=1,
            child_id=1431,
            connected_at=None,
        ),
        EcosystemsChildEcosystems(
            id=35828,
            created_at=datetime.fromisoformat("2022-12-12 07:04:22"),
            parent_id=1,
            child_id=111,
            connected_at=None,
        ),
        EcosystemsChildEcosystems(
            id=5725,
            created_at=datetime.fromisoformat("2021-10-05 20:24:20"),
            parent_id=1,
            child_id=314,
            connected_at=None,
        ),
        EcosystemsChildEcosystems(
            id=2931,
            created_at=datetime.fromisoformat("2020-10-02 20:04:44"),
            parent_id=1,
            child_id=2116,
            connected_at=None,
        ),
        EcosystemsChildEcosystems(
            id=1,
            created_at=datetime.fromisoformat("2019-07-07 01:41:11"),
            parent_id=1,
            child_id=5,
            connected_at=None,
        ),
    ],
)
