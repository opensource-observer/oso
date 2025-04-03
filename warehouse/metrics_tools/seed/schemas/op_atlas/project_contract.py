from datetime import datetime, timedelta

from metrics_tools.seed.loader import DestinationLoader
from metrics_tools.seed.types import Column
from pydantic import BaseModel


class ProjectContract(BaseModel):
    id: str = Column("VARCHAR")
    contract_address: str = Column("VARCHAR")
    deployer_address: str = Column("VARCHAR")
    deployment_hash: str = Column("VARCHAR")
    verification_proof: str = Column("VARCHAR")
    chain_id: int = Column("BIGINT")
    created_at: datetime = Column("TIMESTAMP(6) WITH TIME ZONE")
    updated_at: datetime = Column("TIMESTAMP(6) WITH TIME ZONE")
    project_id: str = Column("VARCHAR")
    description: str | None = Column("VARCHAR")
    name: str | None = Column("VARCHAR")
    dlt_load_id: str = Column("VARCHAR", "_dlt_load_id")
    dlt_id: str = Column("VARCHAR", "_dlt_id")
    verification_chain_id: int | None = Column("BIGINT")


async def seed(loader: DestinationLoader):
    await loader.create_table("op_atlas.project_contract", ProjectContract)

    await loader.insert(
        "op_atlas.project_contract",
        [
            ProjectContract(
                id="1",
                contract_address="0x123",
                deployer_address="0xabc",
                deployment_hash="hash1",
                verification_proof="proof1",
                chain_id=1,
                created_at=datetime.now() - timedelta(days=2),
                updated_at=datetime.now() - timedelta(days=2),
                project_id="proj1",
                description="Description One",
                name="Contract One",
                dlt_load_id="load1",
                dlt_id="dlt1",
                verification_chain_id=1,
            ),
            ProjectContract(
                id="2",
                contract_address="0x456",
                deployer_address="0xdef",
                deployment_hash="hash2",
                verification_proof="proof2",
                chain_id=2,
                created_at=datetime.now() - timedelta(days=1),
                updated_at=datetime.now() - timedelta(days=1),
                project_id="proj2",
                description="Description Two",
                name="Contract Two",
                dlt_load_id="load2",
                dlt_id="dlt2",
                verification_chain_id=2,
            ),
        ],
    )
