from datetime import datetime

from metrics_tools.seed.types import Column, SeedConfig
from pydantic import BaseModel


class Commits(BaseModel):
    """Seed model for opendevdata commits"""

    id: int | None = Column("BIGINT", description="id")
    repo_id: int | None = Column("BIGINT", description="repo id")
    sha1: str | None = Column("VARCHAR", description="sha1")
    created_at: datetime | None = Column("TIMESTAMP", description="created at")
    additions: int | None = Column("BIGINT", description="additions")
    deletions: int | None = Column("BIGINT", description="deletions")
    authored_at: datetime | None = Column("TIMESTAMP", description="authored at")
    authored_at_offset: int | None = Column("BIGINT", description="authored at offset")
    committed_at: datetime | None = Column("TIMESTAMP", description="committed at")
    committed_at_offset: int | None = Column(
        "BIGINT", description="committed at offset"
    )
    commit_author_name: str | None = Column("VARCHAR", description="commit author name")
    commit_author_email: str | None = Column(
        "VARCHAR", description="commit author email"
    )
    canonical_developer_id: int | None = Column(
        "BIGINT", description="canonical developer id"
    )
    is_bot: int | None = Column("BIGINT", description="is bot")


seed = SeedConfig(
    catalog="bigquery",
    schema="opendevdata",
    table="commits",
    base=Commits,
    rows=[
        Commits(
            id=279203346,
            repo_id=2140701,
            sha1="a42c55011e758b7c24d4c15f4781295184b0eceb",
            created_at=datetime.fromisoformat("2025-06-30 02:12:06"),
            additions=4865,
            deletions=4222,
            authored_at=datetime.fromisoformat("2024-02-24 18:47:08"),
            authored_at_offset=0,
            committed_at=datetime.fromisoformat("2024-02-24 18:47:08"),
            committed_at_offset=0,
            commit_author_name="stdlib-bot",
            commit_author_email="noreply@stdlib.io",
            canonical_developer_id=885482,
            is_bot=1,
        ),
        Commits(
            id=279203552,
            repo_id=2140701,
            sha1="c1940e2ae5d6a5539fcf2d7ff377ee40d9094891",
            created_at=datetime.fromisoformat("2025-06-30 02:12:06"),
            additions=7,
            deletions=2,
            authored_at=datetime.fromisoformat("2024-02-24 19:16:13"),
            authored_at_offset=0,
            committed_at=datetime.fromisoformat("2024-02-24 19:16:13"),
            committed_at_offset=0,
            commit_author_name="stdlib-bot",
            commit_author_email="noreply@stdlib.io",
            canonical_developer_id=885482,
            is_bot=1,
        ),
        Commits(
            id=279203539,
            repo_id=2140701,
            sha1="a7a7ffe12f02b3a534d6a7936cf285eac4de432c",
            created_at=datetime.fromisoformat("2025-06-30 02:12:06"),
            additions=6,
            deletions=1,
            authored_at=datetime.fromisoformat("2024-02-24 19:16:14"),
            authored_at_offset=0,
            committed_at=datetime.fromisoformat("2024-02-24 19:16:14"),
            committed_at_offset=0,
            commit_author_name="stdlib-bot",
            commit_author_email="noreply@stdlib.io",
            canonical_developer_id=885482,
            is_bot=1,
        ),
        Commits(
            id=279203411,
            repo_id=2140701,
            sha1="a8d4e6e3bb47f0e9559f3ac9dcc1e8e874584ca4",
            created_at=datetime.fromisoformat("2025-06-30 02:12:06"),
            additions=37,
            deletions=39,
            authored_at=datetime.fromisoformat("2024-02-24 16:09:29"),
            authored_at_offset=0,
            committed_at=datetime.fromisoformat("2024-02-24 16:09:29"),
            committed_at_offset=0,
            commit_author_name="stdlib-bot",
            commit_author_email="noreply@stdlib.io",
            canonical_developer_id=885482,
            is_bot=1,
        ),
        Commits(
            id=279203376,
            repo_id=2140701,
            sha1="c2eb2eee2c1703307a790cb7232433bb9ce2c74e",
            created_at=datetime.fromisoformat("2025-06-30 02:12:06"),
            additions=3,
            deletions=2,
            authored_at=datetime.fromisoformat("2024-02-24 16:58:02"),
            authored_at_offset=0,
            committed_at=datetime.fromisoformat("2024-02-24 16:58:02"),
            committed_at_offset=0,
            commit_author_name="stdlib-bot",
            commit_author_email="noreply@stdlib.io",
            canonical_developer_id=885482,
            is_bot=1,
        ),
    ],
)
