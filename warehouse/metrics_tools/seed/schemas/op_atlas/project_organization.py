from datetime import datetime

from metrics_tools.seed.loader import DestinationLoader
from metrics_tools.seed.types import Column
from pydantic import BaseModel


class ProjectOrganization(BaseModel):
    id: str = Column("VARCHAR")
    created_at: datetime = Column("TIMESTAMP(6) WITH TIME ZONE")
    updated_at: datetime = Column("TIMESTAMP(6) WITH TIME ZONE")
    deleted_at: datetime | None = Column("TIMESTAMP(6) WITH TIME ZONE")
    project_id: str = Column("VARCHAR")
    organization_id: str = Column("VARCHAR")
    dlt_load_id: str = Column("VARCHAR", "_dlt_load_id")
    dlt_id: str = Column("VARCHAR", "_dlt_id")


async def seed(loader: DestinationLoader):
    await loader.create_table("op_atlas.project_organization", ProjectOrganization)

    await loader.insert(
        "op_atlas.project_organization",
        [
            ProjectOrganization(
                id="b9ee1d25-860e-4aa5-aa80-cf48ff5c2473",
                created_at=datetime(2025, 3, 23, 17, 13, 21, 416000),
                updated_at=datetime(2025, 3, 23, 17, 13, 23, 471000),
                deleted_at=None,
                project_id="0x1490a15d46c7707536fc9068da7c7d775f22562b346bf5c95369b03f9e3e7dad",
                organization_id="0xdc657d35031ec0b83ab379362609213e7627679e587ecca26b62d3ad628c6535",
                dlt_load_id="1742818377.7490938",
                dlt_id="NdevF1HflHupNg",
            ),
            ProjectOrganization(
                id="31c20a43-96e7-43a2-997c-068980b0402b",
                created_at=datetime(2025, 3, 25, 5, 33, 6, 102000),
                updated_at=datetime(2025, 3, 25, 5, 33, 8, 608000),
                deleted_at=None,
                project_id="0x68f3271c77c9fd815707cefabcccb85457cfc820b65785d29356419243919365",
                organization_id="0x73d3d11609826f7bf461155891b33e4468925d19968cc7e08c5e1ed7a33dbbdb",
                dlt_load_id="1742904671.6629562",
                dlt_id="CuC7kK33myYchA",
            ),
            ProjectOrganization(
                id="fba0c497-b920-4435-a56d-a35066781844",
                created_at=datetime(2025, 3, 25, 14, 48, 4, 348000),
                updated_at=datetime(2025, 3, 25, 14, 48, 6, 420000),
                deleted_at=None,
                project_id="0xd9e0c75338d41d200ebe8d347cdedea7b648b38452aa45c9cd87bdebee726786",
                organization_id="0xd644132af288877e2766885b748590155eaebd95239b67d4e64d05ae8adfbfdd",
                dlt_load_id="1742991242.7355466",
                dlt_id="3EakcqUc5oQXUg",
            ),
            ProjectOrganization(
                id="fba0c497-b920-4435-a56d-a35066781844",
                created_at=datetime(2025, 3, 25, 14, 48, 4, 348000),
                updated_at=datetime(2025, 3, 25, 14, 48, 6, 420000),
                deleted_at=None,
                project_id="0xd9e0c75338d41d200ebe8d347cdedea7b648b38452aa45c9cd87bdebee726786",
                organization_id="0xd644132af288877e2766885b748590155eaebd95239b67d4e64d05ae8adfbfdd",
                dlt_load_id="1742992293.7080584",
                dlt_id="HEgrn+HEOtW6gQ",
            ),
            ProjectOrganization(
                id="5acb646c-4bb9-4e6a-8246-b95f9397773b",
                created_at=datetime(2025, 3, 25, 19, 41, 42, 653000),
                updated_at=datetime(2025, 3, 25, 19, 41, 44, 743000),
                deleted_at=None,
                project_id="0x0576376ae9134c25737f66a10f5d1b62c4df03301c876dc00a4ff1e4ea2e7bd3",
                organization_id="0x9791b3ca77df18d1968fe55ec0ec33ec764c70712184f199b2f5d18a83f7bee4",
                dlt_load_id="1742991242.7355466",
                dlt_id="xRtzztjE6V3etg",
            ),
        ],
    )
