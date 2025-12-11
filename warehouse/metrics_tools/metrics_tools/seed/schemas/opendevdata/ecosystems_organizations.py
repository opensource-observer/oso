from datetime import datetime

from metrics_tools.seed.types import Column, SeedConfig
from pydantic import BaseModel


class EcosystemsOrganizations(BaseModel):
    """Seed model for opendevdata ecosystems_organizations"""

    id: int | None = Column("BIGINT", description="id")
    created_at: datetime | None = Column("TIMESTAMP", description="created at")
    ecosystem_id: int | None = Column("BIGINT", description="ecosystem id")
    organization_id: int | None = Column("BIGINT", description="organization id")
    is_first_party: int | None = Column("BIGINT", description="is first party")


seed = SeedConfig(
    catalog="bigquery",
    schema="opendevdata",
    table="ecosystems_organizations",
    base=EcosystemsOrganizations,
    rows=[
        EcosystemsOrganizations(
            id=753,
            created_at=datetime.fromisoformat("2019-07-19 00:00:07"),
            ecosystem_id=1,
            organization_id=3546,
            is_first_party=1,
        ),
        EcosystemsOrganizations(
            id=752,
            created_at=datetime.fromisoformat("2019-07-19 00:00:05"),
            ecosystem_id=1,
            organization_id=3545,
            is_first_party=0,
        ),
        EcosystemsOrganizations(
            id=751,
            created_at=datetime.fromisoformat("2019-07-19 00:00:02"),
            ecosystem_id=1,
            organization_id=3544,
            is_first_party=0,
        ),
        EcosystemsOrganizations(
            id=750,
            created_at=datetime.fromisoformat("2019-07-18 23:59:58"),
            ecosystem_id=1,
            organization_id=3543,
            is_first_party=0,
        ),
        EcosystemsOrganizations(
            id=383,
            created_at=datetime.fromisoformat("2019-07-15 22:49:37"),
            ecosystem_id=1,
            organization_id=174,
            is_first_party=1,
        ),
    ],
)
