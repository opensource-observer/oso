from datetime import datetime

from metrics_tools.seed.types import Column, SeedConfig
from pydantic import BaseModel


class Organizations(BaseModel):
    """Seed model for opendevdata organizations"""

    id: int | None = Column("BIGINT", description="id")
    created_at: datetime | None = Column("TIMESTAMP", description="created at")
    name: str | None = Column("VARCHAR", description="name")
    link: str | None = Column("VARCHAR", description="link")
    github_created_at: datetime | None = Column(
        "TIMESTAMP", description="github created at"
    )


seed = SeedConfig(
    catalog="bigquery",
    schema="opendevdata",
    table="organizations",
    base=Organizations,
    rows=[
        Organizations(
            id=5,
            created_at=datetime.fromisoformat("2019-07-05 15:18:12"),
            name="NEM",
            link="https://github.com/NemProject",
            github_created_at=datetime.fromisoformat("2014-06-20 11:07:28"),
        ),
        Organizations(
            id=4,
            created_at=datetime.fromisoformat("2019-07-05 15:18:12"),
            name="IOTA",
            link="https://github.com/iotaledger",
            github_created_at=datetime.fromisoformat("2016-06-24 10:55:18"),
        ),
        Organizations(
            id=3,
            created_at=datetime.fromisoformat("2019-07-05 15:18:12"),
            name="Stellar",
            link="https://github.com/stellar",
            github_created_at=datetime.fromisoformat("2014-04-23 16:49:02"),
        ),
        Organizations(
            id=2,
            created_at=datetime.fromisoformat("2019-07-05 15:18:12"),
            name="EOSIO",
            link="https://github.com/EOSIO",
            github_created_at=datetime.fromisoformat("2017-04-05 16:14:32"),
        ),
        Organizations(
            id=1,
            created_at=datetime.fromisoformat("2019-07-05 15:18:12"),
            name="bitcoincashorg",
            link="https://github.com/bitcoincashorg",
            github_created_at=datetime.fromisoformat("2017-07-25 03:27:01"),
        ),
    ],
)
