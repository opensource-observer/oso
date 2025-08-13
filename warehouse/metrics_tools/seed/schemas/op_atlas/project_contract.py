from datetime import datetime, timedelta

from metrics_tools.seed.types import Column, SeedConfig
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
    dlt_load_id: str = Column("VARCHAR", column_name="_dlt_load_id")
    dlt_id: str = Column("VARCHAR", column_name="_dlt_id")
    verification_chain_id: int | None = Column("BIGINT")


seed = SeedConfig(
    catalog="bigquery",
    schema="op_atlas",
    table="project_contract",
    base=ProjectContract,
    rows=[
        ProjectContract(
            id="cf8b1419-2607-486b-bc94-63f172db9e0d",
            contract_address="0xdE2aE25FB984dd60C77dcF6489Be9ee6438eC195",
            deployer_address="0x892Ff98a46e5bd141E2D12618f4B2Fe6284debac",
            deployment_hash="0x5cd09f4cb5a740e17c57c2b5a0be9613f2e9b7fadcc91d6f8f4d1d5476e41df9",
            verification_proof="0x94369315b7028a44e50b9b876b061e84180338c5f372733c55318256264b53500f17df0dee234952d225c302674c5c9a5d13a6cb5959e326586070f44891d6bd1c",
            chain_id=10,
            created_at=datetime.now() - timedelta(days=2),
            updated_at=datetime.now() - timedelta(days=2),
            project_id="0x08df6e20a3cfabbaf8f34d4f4d048fe7da40447c24be0f3ad513db6f13c755dd",
            description=None,
            name=None,
            dlt_load_id="1739198317.726651",
            dlt_id="UVU+eOFJxnFagw",
            verification_chain_id=None,
        ),
        ProjectContract(
            id="75429f73-69e5-44a2-bf76-66b7be75b0cd",
            contract_address="0x5FF137D4b0FDCD49DcA30c7CF57E578a026d2789",
            deployer_address="0x81ead4918134AE386dbd04346216E20AB8F822C4",
            deployment_hash="0xcddea14be9b486fd1c7311dbaf58fe13f1316eebd16d350bed3573b90e9515b8",
            verification_proof="0x45a72fed635dc10fd4e12b025c3e0ba4f336c735f982d4d645509f06a01365425119d7245e6da3612e431e7f5272cfc2b103d0f8cbe9e52a970c2288e64bdd7b1c",
            chain_id=10,
            created_at=datetime.now() - timedelta(days=1),
            updated_at=datetime.now() - timedelta(days=1),
            project_id="0xb98778ca9ff41446e2bc304f7b5d27f0fa7c2bcd11df19e22d1352c06698a1f6",
            description="",
            name="",
            dlt_load_id="1739198317.726651",
            dlt_id="+flm5Fq1YJmwsA",
            verification_chain_id=None,
        ),
        ProjectContract(
            id="7be9f11a-2dc3-4f1e-b3db-4f3b43fbec7d",
            contract_address="0x0000000071727De22E5E9d8BAf0edAc6f37da032",
            deployer_address="0x81ead4918134AE386dbd04346216E20AB8F822C4",
            deployment_hash="0x1f5b834a37c7d91b9541a2b35f8d0bffcf27d4b0f2656f793478db8c8c029d6a",
            verification_proof="0x0",
            chain_id=10,
            created_at=datetime.now() - timedelta(days=1),
            updated_at=datetime.now() - timedelta(days=1),
            project_id="0xb98778ca9ff41446e2bc304f7b5d27f0fa7c2bcd11df19e22d1352c06698a1f6",
            description=None,
            name=None,
            dlt_load_id="1739198317.726651",
            dlt_id="P6+diJ4LVVtPBA",
            verification_chain_id=None,
        ),
        ProjectContract(
            id="21e282ea-3af8-4160-896c-c1e064f1bb7a",
            contract_address="0x0000000071727De22E5E9d8BAf0edAc6f37da032",
            deployer_address="0x81ead4918134AE386dbd04346216E20AB8F822C4",
            deployment_hash="0xa3382f65bab116e6dfe68ef4d96415515bca45b86072725d45d00df2010ac5b0",
            verification_proof="0x0",
            chain_id=8453,
            created_at=datetime.now() - timedelta(days=2),
            updated_at=datetime.now() - timedelta(days=2),
            project_id="0xb98778ca9ff41446e2bc304f7b5d27f0fa7c2bcd11df19e22d1352c06698a1f6",
            description=None,
            name=None,
            dlt_load_id="1739198317.726651",
            dlt_id="83jQCBKGcu9r/A",
            verification_chain_id=None,
        ),
    ],
)
