from datetime import datetime

from metrics_tools.seed.types import Column, SeedConfig
from pydantic import BaseModel


class EcosystemsRepos(BaseModel):
    """Seed model for opendevdata ecosystems_repos"""

    id: int | None = Column("BIGINT", description="id")
    created_at: datetime | None = Column("TIMESTAMP", description="created at")
    ecosystem_id: int | None = Column("BIGINT", description="ecosystem id")
    repo_id: int | None = Column("BIGINT", description="repo id")
    connected_at: datetime | None = Column("TIMESTAMP", description="connected at")


seed = SeedConfig(
    catalog="bigquery",
    schema="opendevdata",
    table="ecosystems_repos",
    base=EcosystemsRepos,
    rows=[
        EcosystemsRepos(
            id=273256130,
            created_at=datetime.fromisoformat("2025-06-04 17:48:27"),
            ecosystem_id=13732,
            repo_id=495,
            connected_at=None,
        ),
        EcosystemsRepos(
            id=273195966,
            created_at=datetime.fromisoformat("2025-06-04 17:39:53"),
            ecosystem_id=12091,
            repo_id=495,
            connected_at=None,
        ),
        EcosystemsRepos(
            id=273137234,
            created_at=datetime.fromisoformat("2025-06-04 17:13:56"),
            ecosystem_id=12146,
            repo_id=2,
            connected_at=None,
        ),
        EcosystemsRepos(
            id=273073261,
            created_at=datetime.fromisoformat("2025-06-04 17:11:50"),
            ecosystem_id=12083,
            repo_id=422,
            connected_at=None,
        ),
        EcosystemsRepos(
            id=273073260,
            created_at=datetime.fromisoformat("2025-06-04 17:11:50"),
            ecosystem_id=12083,
            repo_id=421,
            connected_at=None,
        ),
    ],
)
