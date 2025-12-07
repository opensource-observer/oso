from datetime import datetime, timedelta

from metrics_tools.seed.types import Column, SeedConfig
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
    dlt_load_id: str = Column("VARCHAR", column_name="_dlt_load_id")
    dlt_id: str = Column("VARCHAR", column_name="_dlt_id")


seed = SeedConfig(
    catalog="bigquery",
    schema="op_atlas",
    table="project",
    base=Project,
    rows=[
        Project(
            id="0xcc8d03e014e121d10602eeff729b755d5dc6a317df0d6302c8a9d3b5424aaba8",
            name="Solidity",
            description="Solidity is an object-oriented, high-level language for implementing smart contracts.",
            category="Utility",
            thumbnail_url="https://storage.googleapis.com/op-atlas/b6f312d0-1025-4a19-baa9-3aa218fe0833.png",
            banner_url="https://storage.googleapis.com/op-atlas/bca65077-a87b-4fd8-bcc3-9ad0a65d9d27.png",
            twitter="https://x.com/solidity_lang",
            mirror="https://soliditylang.org/blog/",
            open_source_observer_slug="",
            added_team_members=True,
            added_funding=True,
            last_metadata_update=datetime.now() - timedelta(days=2),
            created_at=datetime.now() - timedelta(days=2),
            updated_at=datetime.now() - timedelta(days=2),
            deleted_at=None,
            has_code_repositories=True,
            is_on_chain_contract=False,
            pricing_model="free",
            pricing_model_details="",
            is_submitted_to_oso=False,
            dlt_load_id="1745325114.4110816",
            dlt_id="w7iRlKxZn25cdg",
        ),
        Project(
            id="0xcc8d03e014e121d10602eeff729b755d5dc6a317df0d6302c8a9d3b5424aaba8",
            name="Solidity",
            description="Solidity is an object-oriented, high-level language for implementing smart contracts.",
            category="Utility",
            thumbnail_url="https://storage.googleapis.com/op-atlas/b6f312d0-1025-4a19-baa9-3aa218fe0833.png",
            banner_url="https://storage.googleapis.com/op-atlas/bca65077-a87b-4fd8-bcc3-9ad0a65d9d27.png",
            twitter="https://x.com/solidity_lang",
            mirror="https://soliditylang.org/blog/",
            open_source_observer_slug="",
            added_team_members=True,
            added_funding=True,
            last_metadata_update=datetime.now() - timedelta(days=1),
            created_at=datetime.now() - timedelta(days=2),
            updated_at=datetime.now() - timedelta(days=1),
            deleted_at=None,
            has_code_repositories=True,
            is_on_chain_contract=False,
            pricing_model="free",
            pricing_model_details="",
            is_submitted_to_oso=False,
            dlt_load_id="1744117316.5850847",
            dlt_id="vh0m30QNSQHp1g",
        ),
        Project(
            id="0xb98778ca9ff41446e2bc304f7b5d27f0fa7c2bcd11df19e22d1352c06698a1f6",
            name="Account Abstraction - ERC-4337",
            description="The AA team is working on standards for decentralized account abstraction, enabling better UX and security for the next billion users.",
            category="Utility",
            thumbnail_url="https://storage.googleapis.com/op-atlas/35570d3a-c51f-48cd-b236-0098f734dd0e.png",
            banner_url="https://storage.googleapis.com/op-atlas/9c9385ff-9ce2-46a1-9aa1-0e3274a04392.png",
            twitter="https://twitter.com/erc4337",
            mirror=None,
            open_source_observer_slug="eth-infinitism-account-abstraction",
            added_team_members=True,
            added_funding=True,
            last_metadata_update=datetime.now() - timedelta(days=2),
            created_at=datetime.now() - timedelta(days=2),
            updated_at=datetime.now() - timedelta(days=2),
            deleted_at=None,
            has_code_repositories=True,
            is_on_chain_contract=True,
            pricing_model="free",
            pricing_model_details="",
            is_submitted_to_oso=False,
            dlt_load_id="1741695162.057644",
            dlt_id="O9Iu+1cGb3F3Ng",
        ),
        Project(
            id="0x08df6e20a3cfabbaf8f34d4f4d048fe7da40447c24be0f3ad513db6f13c755dd",
            name="Velodrome Finance",
            description="The central trading & liquidity marketplace on Superchain",
            category="DeFi",
            thumbnail_url="https://storage.googleapis.com/op-atlas/438ea57d-059c-4327-82e4-abfc94544bad.png",
            banner_url="https://storage.googleapis.com/op-atlas/2d33616b-bceb-449d-aa0a-b8270b1b3e3b.png",
            twitter="https://twitter.com/VelodromeFi",
            mirror="https://medium.com/@VelodromeFi",
            open_source_observer_slug="velodrome",
            added_team_members=True,
            added_funding=True,
            last_metadata_update=datetime.now() - timedelta(days=1),
            created_at=datetime.now() - timedelta(days=1),
            updated_at=datetime.now() - timedelta(days=1),
            deleted_at=None,
            has_code_repositories=True,
            is_on_chain_contract=True,
            pricing_model="free",
            pricing_model_details="",
            is_submitted_to_oso=True,
            dlt_load_id="1740485260.5537214",
            dlt_id="yMTcvWZwiZs5LA",
        ),
    ],
)
