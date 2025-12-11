from datetime import datetime

from metrics_tools.seed.types import Column, SeedConfig
from pydantic import BaseModel


class Url(BaseModel):
    url: str | None = Column("VARCHAR")


class Social(BaseModel):
    discord: list[Url] | None = Column("ARRAY(ROW(?))")
    farcaster: list[Url] | None = Column("ARRAY(ROW(?))")
    medium: list[Url] | None = Column("ARRAY(ROW(?))")
    mirror: list[Url] | None = Column("ARRAY(ROW(?))")
    reddit: list[Url] | None = Column("ARRAY(ROW(?))")
    telegram: list[Url] | None = Column("ARRAY(ROW(?))")
    twitter: list[Url] | None = Column("ARRAY(ROW(?))")
    youtube: list[Url] | None = Column("ARRAY(ROW(?))")


class Blockchain(BaseModel):
    address: str | None = Column("VARCHAR")
    name: str | None = Column("VARCHAR")
    networks: list[str] | None = Column("ARRAY(VARCHAR)")
    tags: list[str] | None = Column("ARRAY(VARCHAR)")


class Projects(BaseModel):
    version: int | None = Column("BIGINT")
    name: str | None = Column("VARCHAR")
    display_name: str | None = Column("VARCHAR")
    github: list[Url] = Column("ARRAY(ROW(?))")
    description: str | None = Column("VARCHAR")
    websites: list[Url] = Column("ARRAY(ROW(?))")
    social: Social | None = Column("ROW(?)")
    blockchain: list[Blockchain] = Column("ARRAY(ROW(?))")
    npm: list[Url] = Column("ARRAY(ROW(?))")
    go: list[Url] = Column("ARRAY(ROW(?))")
    open_collective: list[Url] = Column("ARRAY(ROW(?))")
    pypi: list[Url] = Column("ARRAY(ROW(?))")
    crates: list[Url] = Column("ARRAY(ROW(?))")
    defillama: list[Url] = Column("ARRAY(ROW(?))")
    sha: bytes | None = Column("VARBINARY")
    committed_time: datetime | None = Column("TIMESTAMP(6) WITH TIME ZONE")


seed = SeedConfig(
    catalog="bigquery",
    schema="ossd",
    table="projects",
    base=Projects,
    rows=[
        Projects(
            version=1,
            name="project1",
            display_name="Project 1",
            github=[Url(url="https://github.com/project1")],
            description="Description 1",
            websites=[Url(url="https://project1.com")],
            social=Social(
                discord=[Url(url="https://discord.com/project1")],
                farcaster=[Url(url="https://warpcast.com/project1")],
                medium=[Url(url="https://medium.com/project1")],
                mirror=[Url(url="https://mirror.xyz/project1")],
                reddit=[Url(url="https://reddit.com/project1")],
                telegram=[Url(url="https://telegram.com/project1")],
                twitter=[Url(url="https://twitter.com/project1")],
                youtube=[Url(url="https://youtube.com/project1")],
            ),
            blockchain=[
                Blockchain(
                    address="address1",
                    name="Blockchain 1",
                    networks=["network1"],
                    tags=["tag1"],
                )
            ],
            npm=[Url(url="https://npmjs.com/project1")],
            go=[Url(url="https://go.com/project1")],
            open_collective=[Url(url="https://opencollective.com/project1")],
            pypi=[Url(url="https://pypi.org/project1")],
            crates=[Url(url="https://crates.io/project1")],
            defillama=[Url(url="https://defillama.com/protocol/project1")],
            sha=None,
            committed_time=datetime.now(),
        ),
        Projects(
            version=2,
            name="project2",
            display_name="Project 2",
            github=[Url(url="https://github.com/project2")],
            description="Description 2",
            websites=[Url(url="https://project2.com")],
            social=Social(
                discord=[Url(url="https://discord.com/project2")],
                farcaster=[Url(url="https://farcaster.xyz/project2")],
                medium=[Url(url="https://medium.com/project2")],
                mirror=[Url(url="https://mirror.xyz/project2")],
                reddit=[Url(url="https://reddit.com/project2")],
                telegram=[Url(url="https://telegram.com/project2")],
                twitter=[Url(url="https://twitter.com/project2")],
                youtube=[Url(url="https://youtube.com/project2")],
            ),
            blockchain=[
                Blockchain(
                    address="address2",
                    name="Blockchain 2",
                    networks=["network2"],
                    tags=["tag2"],
                )
            ],
            npm=[Url(url="https://npmjs.com/project2")],
            go=[Url(url="https://go.com/project2")],
            open_collective=[Url(url="https://opencollective.com/project2")],
            pypi=[Url(url="https://pypi.org/project2")],
            crates=[Url(url="https://crates.io/project2")],
            defillama=[Url(url="https://defillama.com/protocol/project2")],
            sha=None,
            committed_time=datetime.now(),
        ),
    ],
)
