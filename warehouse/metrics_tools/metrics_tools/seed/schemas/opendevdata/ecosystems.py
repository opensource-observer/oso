from datetime import date

from metrics_tools.seed.types import Column, SeedConfig
from pydantic import BaseModel


class Ecosystems(BaseModel):
    """Seed model for opendevdata ecosystems"""

    id: int | None = Column("BIGINT", description="id")
    launch_date: date | None = Column("DATE", description="launch date")
    earliest_first_party_commit_date: date | None = Column(
        "DATE", description="earliest first party commit date"
    )
    earliest_first_party_repo_id: int | None = Column(
        "BIGINT", description="earliest first party repo id"
    )
    earliest_repo_commit_date: date | None = Column(
        "DATE", description="earliest repo commit date"
    )
    earliest_repo_id: int | None = Column("BIGINT", description="earliest repo id")
    derived_launch_date: date | None = Column("DATE", description="derived launch date")
    name: str | None = Column("VARCHAR", description="name")
    is_crypto: int | None = Column("BIGINT", description="is crypto")
    is_category: int | None = Column("BIGINT", description="is category")
    is_virtual: int | None = Column("BIGINT", description="is virtual")
    is_chain: int | None = Column("BIGINT", description="is chain")
    is_multichain: int | None = Column("BIGINT", description="is multichain")


seed = SeedConfig(
    catalog="bigquery",
    schema="opendevdata",
    table="ecosystems",
    base=Ecosystems,
    rows=[
        Ecosystems(
            id=102,
            launch_date=None,
            earliest_first_party_commit_date=None,
            earliest_first_party_repo_id=None,
            earliest_repo_commit_date=None,
            earliest_repo_id=None,
            derived_launch_date=None,
            name="LATOKEN",
            is_crypto=1,
            is_category=0,
            is_virtual=0,
            is_chain=0,
            is_multichain=0,
        ),
        Ecosystems(
            id=95,
            launch_date=None,
            earliest_first_party_commit_date=None,
            earliest_first_party_repo_id=None,
            earliest_repo_commit_date=None,
            earliest_repo_id=None,
            derived_launch_date=None,
            name="QASH",
            is_crypto=1,
            is_category=0,
            is_virtual=0,
            is_chain=0,
            is_multichain=0,
        ),
        Ecosystems(
            id=93,
            launch_date=None,
            earliest_first_party_commit_date=None,
            earliest_first_party_repo_id=None,
            earliest_repo_commit_date=None,
            earliest_repo_id=None,
            derived_launch_date=None,
            name="Power Ledger",
            is_crypto=1,
            is_category=0,
            is_virtual=0,
            is_chain=0,
            is_multichain=0,
        ),
        Ecosystems(
            id=85,
            launch_date=None,
            earliest_first_party_commit_date=None,
            earliest_first_party_repo_id=None,
            earliest_repo_commit_date=None,
            earliest_repo_id=None,
            derived_launch_date=None,
            name="Linkey",
            is_crypto=1,
            is_category=0,
            is_virtual=0,
            is_chain=0,
            is_multichain=0,
        ),
        Ecosystems(
            id=64,
            launch_date=None,
            earliest_first_party_commit_date=None,
            earliest_first_party_repo_id=None,
            earliest_repo_commit_date=None,
            earliest_repo_id=None,
            derived_launch_date=None,
            name="REPO",
            is_crypto=1,
            is_category=0,
            is_virtual=0,
            is_chain=0,
            is_multichain=0,
        ),
    ],
)
