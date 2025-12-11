from datetime import datetime

from metrics_tools.seed.types import Column, SeedConfig
from pydantic import BaseModel


class Repos(BaseModel):
    """Seed model for opendevdata repos"""

    id: int | None = Column("BIGINT", description="id")
    created_at: datetime | None = Column("TIMESTAMP", description="created at")
    repo_created_at: datetime | None = Column(
        "TIMESTAMP", description="repo created at"
    )
    name: str | None = Column("VARCHAR", description="name")
    github_graphql_id: str | None = Column("VARCHAR", description="github graphql id")
    link: str | None = Column("VARCHAR", description="link")
    organization_id: int | None = Column("BIGINT", description="organization id")
    num_stars: int | None = Column("BIGINT", description="num stars")
    num_forks: int | None = Column("BIGINT", description="num forks")
    num_issues: int | None = Column("BIGINT", description="num issues")
    is_blacklist: int | None = Column("BIGINT", description="is blacklist")


seed = SeedConfig(
    catalog="bigquery",
    schema="opendevdata",
    table="repos",
    base=Repos,
    rows=[
        Repos(
            id=4,
            created_at=datetime.fromisoformat("2019-05-31 02:53:44"),
            repo_created_at=datetime.fromisoformat("2017-04-05 17:09:53"),
            name="EOSIO/eos",
            github_graphql_id="R_kgDOBTSkLA",
            link="https://github.com/EOSIO/eos",
            organization_id=2,
            num_stars=11246,
            num_forks=3661,
            num_issues=5054,
            is_blacklist=0,
        ),
        Repos(
            id=7,
            created_at=datetime.fromisoformat("2019-05-31 02:53:44"),
            repo_created_at=datetime.fromisoformat("2017-06-06 07:55:17"),
            name="EOSIO/Documentation",
            github_graphql_id="R_kgDOBZKRoQ",
            link="https://github.com/EOSIO/Documentation",
            organization_id=2,
            num_stars=2057,
            num_forks=870,
            num_issues=48,
            is_blacklist=0,
        ),
        Repos(
            id=9,
            created_at=datetime.fromisoformat("2019-05-31 02:53:44"),
            repo_created_at=datetime.fromisoformat("2017-08-03 18:17:52"),
            name="EOSIO/eosjs",
            github_graphql_id="R_kgDOBeqfuQ",
            link="https://github.com/EOSIO/eosjs",
            organization_id=2,
            num_stars=1434,
            num_forks=458,
            num_issues=565,
            is_blacklist=0,
        ),
        Repos(
            id=8,
            created_at=datetime.fromisoformat("2019-05-31 02:53:44"),
            repo_created_at=datetime.fromisoformat("2017-06-09 18:01:20"),
            name="EOSIO/eos-token-distribution",
            github_graphql_id="R_kgDOBZiPlQ",
            link="https://github.com/EOSIO/eos-token-distribution",
            organization_id=2,
            num_stars=192,
            num_forks=144,
            num_issues=28,
            is_blacklist=0,
        ),
        Repos(
            id=3,
            created_at=datetime.fromisoformat("2019-05-31 02:53:44"),
            repo_created_at=datetime.fromisoformat("2017-12-19 00:53:18"),
            name="bitcoincashorg/workgroups",
            github_graphql_id="R_kgDOBtY5TA",
            link="https://github.com/bitcoincashorg/workgroups",
            organization_id=1,
            num_stars=37,
            num_forks=20,
            num_issues=1,
            is_blacklist=0,
        ),
    ],
)
