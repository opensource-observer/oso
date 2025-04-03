from datetime import datetime, timedelta

from metrics_tools.seed.loader import DestinationLoader
from metrics_tools.seed.types import Column
from pydantic import BaseModel


class Project(BaseModel):
    id: str = Column("VARCHAR")
    name: str = Column("VARCHAR")
    description: str | None = Column("VARCHAR")
    category: str | None = Column("VARCHAR")
    thumbnail_url: str | None = Column("VARCHAR")
    banner_url: str | None = Column("VARCHAR")
    twitter: str | None = Column("VARCHAR")
    mirror: str | None = Column("VARCHAR")
    open_source_observer_slug: str | None = Column("VARCHAR")
    added_team_members: bool = Column("BOOLEAN")
    added_funding: bool = Column("BOOLEAN")
    last_metadata_update: datetime = Column("TIMESTAMP(6) WITH TIME ZONE")
    created_at: datetime = Column("TIMESTAMP(6) WITH TIME ZONE")
    updated_at: datetime = Column("TIMESTAMP(6) WITH TIME ZONE")
    deleted_at: datetime | None = Column("TIMESTAMP(6) WITH TIME ZONE")
    has_code_repositories: bool = Column("BOOLEAN")
    is_on_chain_contract: bool = Column("BOOLEAN")
    pricing_model: str | None = Column("VARCHAR")
    pricing_model_details: str | None = Column("VARCHAR")
    is_submitted_to_oso: bool = Column("BOOLEAN")
    dlt_load_id: str = Column("VARCHAR", "_dlt_load_id")
    dlt_id: str = Column("VARCHAR", "_dlt_id")


async def seed(loader: DestinationLoader):
    await loader.create_table("op_atlas.project", Project)

    await loader.insert(
        "op_atlas.project",
        [
            Project(
                id="1",
                name="Project One",
                description="Description One",
                category="Category One",
                thumbnail_url="http://thumbnail1.com",
                banner_url="http://banner1.com",
                twitter="twitter1",
                mirror="mirror1",
                open_source_observer_slug="slug1",
                added_team_members=True,
                added_funding=True,
                last_metadata_update=datetime.now() - timedelta(days=2),
                created_at=datetime.now() - timedelta(days=2),
                updated_at=datetime.now() - timedelta(days=2),
                deleted_at=None,
                has_code_repositories=True,
                is_on_chain_contract=True,
                pricing_model="model1",
                pricing_model_details="details1",
                is_submitted_to_oso=True,
                dlt_load_id="load1",
                dlt_id="dlt1",
            ),
            Project(
                id="2",
                name="Project Two",
                description="Description Two",
                category="Category Two",
                thumbnail_url="http://thumbnail2.com",
                banner_url="http://banner2.com",
                twitter="twitter2",
                mirror="mirror2",
                open_source_observer_slug="slug2",
                added_team_members=False,
                added_funding=False,
                last_metadata_update=datetime.now() - timedelta(days=1),
                created_at=datetime.now() - timedelta(days=1),
                updated_at=datetime.now() - timedelta(days=1),
                deleted_at=None,
                has_code_repositories=False,
                is_on_chain_contract=False,
                pricing_model="model2",
                pricing_model_details="details2",
                is_submitted_to_oso=False,
                dlt_load_id="load2",
                dlt_id="dlt2",
            ),
        ],
    )
