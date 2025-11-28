from datetime import date, datetime
from typing import List, Optional

from metrics_tools.seed.types import Column, SeedConfig
from pydantic import BaseModel


class IntElement(BaseModel):
    element: int


class IntList(BaseModel):
    list: List[IntElement]


class DateElement(BaseModel):
    element: date


class DateList(BaseModel):
    list: List[DateElement]


class EcosystemsChildEcosystemsRecursive(BaseModel):
    """Seed model for opendevdata ecosystems_child_ecosystems_recursive"""

    parent_id: int | None = Column("BIGINT", description="parent id")
    child_id: int | None = Column("BIGINT", description="child id")
    created_at: datetime | None = Column("TIMESTAMP", description="created at")
    ecosystem_ecosystem_paths: Optional[IntList] = Column(
        "ROW(list ARRAY(ROW(element BIGINT)))",
        description="ecosystem ecosystem paths",
    )
    ecosystem_chain_ecosystem_paths: Optional[IntList] = Column(
        "ROW(list ARRAY(ROW(element BIGINT)))",
        description="ecosystem chain ecosystem paths",
    )
    connection_dates: Optional[DateList] = Column(
        "ROW(list ARRAY(ROW(element DATE)))", description="connection dates"
    )
    connected_at: date | None = Column("DATE", description="connected at")


seed = SeedConfig(
    catalog="bigquery",
    schema="opendevdata",
    table="ecosystems_child_ecosystems_recursive",
    base=EcosystemsChildEcosystemsRecursive,
    rows=[
        EcosystemsChildEcosystemsRecursive(
            parent_id=12,
            child_id=86,
            created_at=datetime.fromisoformat("2024-10-24 15:40:11"),
            ecosystem_ecosystem_paths=IntList(
                list=[
                    IntElement(element=12),
                    IntElement(element=9503),
                    IntElement(element=11554),
                    IntElement(element=9455),
                    IntElement(element=2),
                    IntElement(element=7089),
                    IntElement(element=86),
                ]
            ),
            ecosystem_chain_ecosystem_paths=IntList(
                list=[IntElement(element=2), IntElement(element=7089)]
            ),
            connection_dates=DateList(
                list=[
                    DateElement(element=date.fromisoformat("2013-12-26")),
                    DateElement(element=date.fromisoformat("2013-12-26")),
                    DateElement(element=date.fromisoformat("2022-12-01")),
                    DateElement(element=date.fromisoformat("2022-12-01")),
                    DateElement(element=date.fromisoformat("2022-12-01")),
                    DateElement(element=date.fromisoformat("2020-03-22")),
                    DateElement(element=date.fromisoformat("2015-07-30")),
                    DateElement(element=date.fromisoformat("2015-07-30")),
                    DateElement(element=date.fromisoformat("2021-01-16")),
                    DateElement(element=date.fromisoformat("2021-01-16")),
                    DateElement(element=date.fromisoformat("2021-01-16")),
                    DateElement(element=date.fromisoformat("2018-04-18")),
                ]
            ),
            connected_at=date.fromisoformat("2022-12-01"),
        ),
        EcosystemsChildEcosystemsRecursive(
            parent_id=12,
            child_id=83,
            created_at=datetime.fromisoformat("2024-11-09 00:00:17"),
            ecosystem_ecosystem_paths=IntList(
                list=[
                    IntElement(element=12),
                    IntElement(element=9503),
                    IntElement(element=11554),
                    IntElement(element=9455),
                    IntElement(element=2),
                    IntElement(element=7089),
                    IntElement(element=83),
                ]
            ),
            ecosystem_chain_ecosystem_paths=IntList(
                list=[IntElement(element=2), IntElement(element=7089)]
            ),
            connection_dates=DateList(
                list=[
                    DateElement(element=date.fromisoformat("2013-12-26")),
                    DateElement(element=date.fromisoformat("2013-12-26")),
                    DateElement(element=date.fromisoformat("2022-12-01")),
                    DateElement(element=date.fromisoformat("2022-12-01")),
                    DateElement(element=date.fromisoformat("2022-12-01")),
                    DateElement(element=date.fromisoformat("2020-03-22")),
                    DateElement(element=date.fromisoformat("2015-07-30")),
                    DateElement(element=date.fromisoformat("2015-07-30")),
                    DateElement(element=date.fromisoformat("2021-01-16")),
                    DateElement(element=date.fromisoformat("2021-01-16")),
                    DateElement(element=date.fromisoformat("2021-01-16")),
                    DateElement(element=date.fromisoformat("2018-04-30")),
                ]
            ),
            connected_at=date.fromisoformat("2022-12-01"),
        ),
        EcosystemsChildEcosystemsRecursive(
            parent_id=12,
            child_id=83,
            created_at=datetime.fromisoformat("2024-11-09 00:00:17"),
            ecosystem_ecosystem_paths=IntList(
                list=[
                    IntElement(element=12),
                    IntElement(element=9503),
                    IntElement(element=11435),
                    IntElement(element=9455),
                    IntElement(element=2),
                    IntElement(element=7089),
                    IntElement(element=83),
                ]
            ),
            ecosystem_chain_ecosystem_paths=IntList(
                list=[IntElement(element=2), IntElement(element=7089)]
            ),
            connection_dates=DateList(
                list=[
                    DateElement(element=date.fromisoformat("2013-12-26")),
                    DateElement(element=date.fromisoformat("2013-12-26")),
                    DateElement(element=date.fromisoformat("2018-09-21")),
                    DateElement(element=date.fromisoformat("2018-09-21")),
                    DateElement(element=date.fromisoformat("2020-03-22")),
                    DateElement(element=date.fromisoformat("2020-03-22")),
                    DateElement(element=date.fromisoformat("2015-07-30")),
                    DateElement(element=date.fromisoformat("2015-07-30")),
                    DateElement(element=date.fromisoformat("2021-01-16")),
                    DateElement(element=date.fromisoformat("2021-01-16")),
                    DateElement(element=date.fromisoformat("2021-01-16")),
                    DateElement(element=date.fromisoformat("2018-04-30")),
                ]
            ),
            connected_at=date.fromisoformat("2021-01-16"),
        ),
        EcosystemsChildEcosystemsRecursive(
            parent_id=12,
            child_id=78,
            created_at=datetime.fromisoformat("2024-10-24 15:40:11"),
            ecosystem_ecosystem_paths=IntList(
                list=[
                    IntElement(element=12),
                    IntElement(element=9503),
                    IntElement(element=11554),
                    IntElement(element=9455),
                    IntElement(element=2),
                    IntElement(element=9562),
                    IntElement(element=78),
                ]
            ),
            ecosystem_chain_ecosystem_paths=IntList(
                list=[
                    IntElement(element=2),
                    IntElement(element=9562),
                    IntElement(element=78),
                ]
            ),
            connection_dates=DateList(
                list=[
                    DateElement(element=date.fromisoformat("2013-12-26")),
                    DateElement(element=date.fromisoformat("2013-12-26")),
                    DateElement(element=date.fromisoformat("2022-12-01")),
                    DateElement(element=date.fromisoformat("2022-12-01")),
                    DateElement(element=date.fromisoformat("2022-12-01")),
                    DateElement(element=date.fromisoformat("2020-03-22")),
                    DateElement(element=date.fromisoformat("2015-07-30")),
                    DateElement(element=date.fromisoformat("2015-07-30")),
                    DateElement(element=date.fromisoformat("2020-09-11")),
                    DateElement(element=date.fromisoformat("2020-09-11")),
                    DateElement(element=date.fromisoformat("2020-09-11")),
                    DateElement(element=date.fromisoformat("2018-09-08")),
                ]
            ),
            connected_at=date.fromisoformat("2022-12-01"),
        ),
        EcosystemsChildEcosystemsRecursive(
            parent_id=12,
            child_id=78,
            created_at=datetime.fromisoformat("2024-10-24 15:40:11"),
            ecosystem_ecosystem_paths=IntList(
                list=[
                    IntElement(element=12),
                    IntElement(element=9503),
                    IntElement(element=11435),
                    IntElement(element=9455),
                    IntElement(element=2),
                    IntElement(element=9562),
                    IntElement(element=78),
                ]
            ),
            ecosystem_chain_ecosystem_paths=IntList(
                list=[
                    IntElement(element=2),
                    IntElement(element=9562),
                    IntElement(element=78),
                ]
            ),
            connection_dates=DateList(
                list=[
                    DateElement(element=date.fromisoformat("2013-12-26")),
                    DateElement(element=date.fromisoformat("2013-12-26")),
                    DateElement(element=date.fromisoformat("2018-09-21")),
                    DateElement(element=date.fromisoformat("2018-09-21")),
                    DateElement(element=date.fromisoformat("2020-03-22")),
                    DateElement(element=date.fromisoformat("2020-03-22")),
                    DateElement(element=date.fromisoformat("2015-07-30")),
                    DateElement(element=date.fromisoformat("2015-07-30")),
                    DateElement(element=date.fromisoformat("2020-09-11")),
                    DateElement(element=date.fromisoformat("2020-09-11")),
                    DateElement(element=date.fromisoformat("2020-09-11")),
                    DateElement(element=date.fromisoformat("2018-09-08")),
                ]
            ),
            connected_at=date.fromisoformat("2020-09-11"),
        ),
    ],
)
