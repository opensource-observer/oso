from datetime import date

from metrics_tools.seed.types import Column, SeedConfig
from pydantic import BaseModel


class EcoMads(BaseModel):
    """Seed model for opendevdata eco_mads"""

    ecosystem_id: int | None = Column("BIGINT", description="ecosystem id")
    day: date | None = Column("DATE", description="day")
    all_devs: int | None = Column("BIGINT", description="all devs")
    exclusive_devs: int | None = Column("BIGINT", description="exclusive devs")
    multichain_devs: int | None = Column("BIGINT", description="multichain devs")
    num_commits: int | None = Column("BIGINT", description="num commits")
    devs_0_1y: int | None = Column("BIGINT", description="devs 0 1y")
    devs_1_2y: int | None = Column("BIGINT", description="devs 1 2y")
    devs_2y_plus: int | None = Column("BIGINT", description="devs 2y plus")
    one_time_devs: int | None = Column("BIGINT", description="one time devs")
    part_time_devs: int | None = Column("BIGINT", description="part time devs")
    full_time_devs: int | None = Column("BIGINT", description="full time devs")


seed = SeedConfig(
    catalog="bigquery",
    schema="opendevdata",
    table="eco_mads",
    base=EcoMads,
    rows=[
        EcoMads(
            ecosystem_id=1,
            day=date.fromisoformat("2015-02-02"),
            all_devs=299,
            exclusive_devs=275,
            multichain_devs=24,
            num_commits=6059,
            devs_0_1y=197,
            devs_1_2y=71,
            devs_2y_plus=31,
            one_time_devs=80,
            part_time_devs=157,
            full_time_devs=62,
        ),
        EcoMads(
            ecosystem_id=1,
            day=date.fromisoformat("2015-01-18"),
            all_devs=267,
            exclusive_devs=237,
            multichain_devs=30,
            num_commits=5106,
            devs_0_1y=183,
            devs_1_2y=57,
            devs_2y_plus=27,
            one_time_devs=65,
            part_time_devs=138,
            full_time_devs=64,
        ),
        EcoMads(
            ecosystem_id=1,
            day=date.fromisoformat("2015-01-15"),
            all_devs=266,
            exclusive_devs=234,
            multichain_devs=32,
            num_commits=5103,
            devs_0_1y=178,
            devs_1_2y=61,
            devs_2y_plus=27,
            one_time_devs=58,
            part_time_devs=148,
            full_time_devs=60,
        ),
        EcoMads(
            ecosystem_id=1,
            day=date.fromisoformat("2015-01-06"),
            all_devs=265,
            exclusive_devs=236,
            multichain_devs=29,
            num_commits=4820,
            devs_0_1y=185,
            devs_1_2y=54,
            devs_2y_plus=26,
            one_time_devs=60,
            part_time_devs=147,
            full_time_devs=58,
        ),
        EcoMads(
            ecosystem_id=1,
            day=date.fromisoformat("2015-01-11"),
            all_devs=259,
            exclusive_devs=229,
            multichain_devs=30,
            num_commits=4808,
            devs_0_1y=174,
            devs_1_2y=58,
            devs_2y_plus=27,
            one_time_devs=51,
            part_time_devs=144,
            full_time_devs=64,
        ),
    ],
)
