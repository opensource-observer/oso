from datetime import datetime

from metrics_tools.seed.loader import DestinationLoader
from metrics_tools.seed.types import Column
from pydantic import BaseModel


class Repo(BaseModel):
    id: int | None = Column("BIGINT")
    name: str | None = Column("VARCHAR")
    url: str | None = Column("VARCHAR")


class Actor(BaseModel):
    id: int | None = Column("BIGINT")
    login: str | None = Column("VARCHAR")
    gravatar_id: str | None = Column("VARCHAR")
    avatar_url: str | None = Column("VARCHAR")
    url: str | None = Column("VARCHAR")


class Org(BaseModel):
    id: int | None = Column("BIGINT")
    login: str | None = Column("VARCHAR")
    gravatar_id: str | None = Column("VARCHAR")
    avatar_url: str | None = Column("VARCHAR")
    url: str | None = Column("VARCHAR")


class StgGithubEvents(BaseModel):
    type: str | None = Column("VARCHAR")
    public: bool | None = Column("BOOLEAN")
    payload: str | None = Column("VARCHAR")
    repo: Repo | None = Column("ROW(?)")
    actor: Actor | None = Column("ROW(?)")
    org: Org | None = Column("ROW(?)")
    created_at: datetime | None = Column("TIMESTAMP(6) WITH TIME ZONE")
    id: str | None = Column("VARCHAR")
    other: str | None = Column("VARCHAR")


async def seed(loader: DestinationLoader):
    await loader.create_table("oso.stg_github__events", StgGithubEvents)

    await loader.insert(
        "oso.stg_github__events",
        [
            StgGithubEvents(
                type="type1",
                public=True,
                payload="payload1",
                repo=Repo(id=1, name="repo1", url="url1"),
                actor=Actor(
                    id=1,
                    login="login1",
                    gravatar_id="gravatar1",
                    avatar_url="avatar1",
                    url="url1",
                ),
                org=Org(
                    id=1,
                    login="login1",
                    gravatar_id="gravatar1",
                    avatar_url="avatar1",
                    url="url1",
                ),
                created_at=datetime.now(),
                id="id1",
                other="other1",
            ),
            StgGithubEvents(
                type="type2",
                public=False,
                payload="payload2",
                repo=Repo(id=2, name="repo2", url="url2"),
                actor=Actor(
                    id=2,
                    login="login2",
                    gravatar_id="gravatar2",
                    avatar_url="avatar2",
                    url="url2",
                ),
                org=Org(
                    id=2,
                    login="login2",
                    gravatar_id="gravatar2",
                    avatar_url="avatar2",
                    url="url2",
                ),
                created_at=datetime.now(),
                id="id2",
                other="other2",
            ),
        ],
    )
