from datetime import datetime, timedelta

from metrics_tools.seed.types import Column, SeedConfig
from pydantic import BaseModel


class ProjectRepository(BaseModel):
    id: str = Column("VARCHAR")
    type: str = Column("VARCHAR")
    url: str = Column("VARCHAR")
    verified: bool = Column("BOOLEAN")
    open_source: bool = Column("BOOLEAN")
    contains_contracts: bool = Column("BOOLEAN")
    created_at: datetime = Column("TIMESTAMP(6) WITH TIME ZONE")
    updated_at: datetime = Column("TIMESTAMP(6) WITH TIME ZONE")
    project_id: str = Column("VARCHAR")
    description: str | None = Column("VARCHAR")
    name: str | None = Column("VARCHAR")
    crate: bool = Column("BOOLEAN")
    npm_package: bool = Column("BOOLEAN")
    dlt_load_id: str = Column("VARCHAR", column_name="_dlt_load_id")
    dlt_id: str = Column("VARCHAR", column_name="_dlt_id")


seed = SeedConfig(
    catalog="bigquery",
    schema="op_atlas",
    table="project_repository",
    base=ProjectRepository,
    rows=[
        ProjectRepository(
            id="af02d93e-a630-44b4-a065-f3404420e329",
            type="github",
            url="https://github.com/eth-infinitism/account-abstraction",
            verified=True,
            open_source=True,
            contains_contracts=False,
            created_at=datetime.now() - timedelta(days=2),
            updated_at=datetime.now() - timedelta(days=2),
            project_id="0xb98778ca9ff41446e2bc304f7b5d27f0fa7c2bcd11df19e22d1352c06698a1f6",
            description="",
            name="",
            crate=False,
            npm_package=False,
            dlt_load_id="1739198854.5956185",
            dlt_id="y/87BaWVmI4IJA",
        ),
        ProjectRepository(
            id="64c38bdf-abd0-4496-b54e-a211876591e4",
            type="github",
            url="https://github.com/ethereum/solidity",
            verified=True,
            open_source=True,
            contains_contracts=True,
            created_at=datetime.now() - timedelta(days=1),
            updated_at=datetime.now() - timedelta(days=1),
            project_id="0xcc8d03e014e121d10602eeff729b755d5dc6a317df0d6302c8a9d3b5424aaba8",
            description="Official GitHub open source repository for Solidity—an object-oriented, high-level language for implementing smart contracts. 🌐",
            name="Solidity GitHub repository",
            crate=False,
            npm_package=False,
            dlt_load_id="1739198854.5956185",
            dlt_id="YNlzJ0rhOkjzxQ",
        ),
        ProjectRepository(
            id="8a435ced-c19b-42af-ad98-50a3493912aa",
            type="github",
            url="https://github.com/velodrome-finance/contracts",
            verified=True,
            open_source=False,
            contains_contracts=True,
            created_at=datetime.now() - timedelta(days=2),
            updated_at=datetime.now() - timedelta(days=2),
            project_id="0x08df6e20a3cfabbaf8f34d4f4d048fe7da40447c24be0f3ad513db6f13c755dd",
            description=None,
            name=None,
            crate=False,
            npm_package=False,
            dlt_load_id="1739198854.5956185",
            dlt_id="QvOh044DorAUow",
        ),
    ],
)
