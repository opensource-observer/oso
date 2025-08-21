from metrics_tools.seed.types import Column, SeedConfig
from pydantic import BaseModel


class LabelsDecoded(BaseModel):
    """Stores decoded labels from the Open Labels Initiative"""

    id: str | None = Column("VARCHAR", description="Unique identifier for the label")
    chain_id: str | None = Column(
        "VARCHAR", description="Chain identifier in eip155 format"
    )
    address: str | None = Column("VARCHAR", description="The address being labeled")
    tag_id: str | None = Column("VARCHAR", description="The type of label")
    tag_value: str | None = Column("VARCHAR", description="The value of the label")
    attester: str | None = Column(
        "VARCHAR", description="Address of the entity that attested the label"
    )
    time_created: int | None = Column(
        "INTEGER", description="Unix timestamp when the label was created"
    )
    revocation_time: int | None = Column(
        "INTEGER", description="Unix timestamp when the label was revoked"
    )
    revoked: bool | None = Column(
        "BOOLEAN", description="Whether the label has been revoked"
    )
    is_offchain: bool | None = Column(
        "BOOLEAN", description="Whether the label is stored offchain"
    )


seed = SeedConfig(
    catalog="bigquery",
    schema="openlabelsinitiative",
    table="labels_decoded",
    base=LabelsDecoded,
    rows=[
        # Original test data
        LabelsDecoded(
            id="0xb5c7aed75a7381094edf2c2b069d1a76fefdbc401ad29321f90eedfad4d7b33f",
            chain_id="eip155:10",
            address="0xfFeE5202B20A364c32DfdA7ad05cccCA83141fa9",
            tag_id="is_eoa",
            tag_value="false",
            attester="0xA725646c05e6Bb813d98C5aBB4E72DF4bcF00B56",
            time_created=1744237337,
            revocation_time=0,
            revoked=False,
            is_offchain=True,
        ),
        LabelsDecoded(
            id="0xb5c7aed75a7381094edf2c2b069d1a76fefdbc401ad29321f90eedfad4d7b33f",
            chain_id="eip155:10",
            address="0xfFeE5202B20A364c32DfdA7ad05cccCA83141fa9",
            tag_id="is_proxy",
            tag_value="true",
            attester="0xA725646c05e6Bb813d98C5aBB4E72DF4bcF00B56",
            time_created=1744237337,
            revocation_time=0,
            revoked=False,
            is_offchain=True,
        ),
        # EOA address
        LabelsDecoded(
            id="0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef",
            chain_id="eip155:any",
            address="0x742d35Cc6634C0532925a3b844Bc454e4438f44e",
            tag_id="is_eoa",
            tag_value="true",
            attester="0xA725646c05e6Bb813d98C5aBB4E72DF4bcF00B56",
            time_created=1744237337,
            revocation_time=0,
            revoked=False,
            is_offchain=True,
        ),
        # Factory contract
        LabelsDecoded(
            id="0xabcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890",
            chain_id="eip155:1",
            address="0x1F98431c8aD98523631AE4a59f267346ea31F984",
            tag_id="is_factory_contract",
            tag_value="true",
            attester="0xA725646c05e6Bb813d98C5aBB4E72DF4bcF00B56",
            time_created=1744237337,
            revocation_time=0,
            revoked=False,
            is_offchain=True,
        ),
        # Paymaster
        LabelsDecoded(
            id="0x7890abcdef1234567890abcdef1234567890abcdef1234567890abcdef123456",
            chain_id="eip155:8453",
            address="0x5FF137D4b0FDCD49DcA30c7CF57E578a026d2789",
            tag_id="is_paymaster",
            tag_value="true",
            attester="0xA725646c05e6Bb813d98C5aBB4E72DF4bcF00B56",
            time_created=1744237337,
            revocation_time=0,
            revoked=False,
            is_offchain=True,
        ),
        # Safe contract
        LabelsDecoded(
            id="0x4567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef123",
            chain_id="eip155:1",
            address="0x3E5c63644E683549055b9Be8653de26E0B4CD36E",
            tag_id="is_safe_contract",
            tag_value="true",
            attester="0xA725646c05e6Bb813d98C5aBB4E72DF4bcF00B56",
            time_created=1744237337,
            revocation_time=0,
            revoked=False,
            is_offchain=True,
        ),
        # Deployer address
        LabelsDecoded(
            id="0xdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890abc",
            chain_id="eip155:1",
            address="0xDeployerContract",
            tag_id="deployer_address",
            tag_value="0xDeployedContract",
            attester="0xA725646c05e6Bb813d98C5aBB4E72DF4bcF00B56",
            time_created=1744237337,
            revocation_time=0,
            revoked=False,
            is_offchain=True,
        ),
        # ERC type
        LabelsDecoded(
            id="0xabc1234567890abcdef1234567890abcdef1234567890abcdef1234567890def",
            chain_id="eip155:1",
            address="0x6B175474E89094C44Da98b954EedeAC495271d0F",
            tag_id="erc_type",
            tag_value='["erc20"]',
            attester="0xA725646c05e6Bb813d98C5aBB4E72DF4bcF00B56",
            time_created=1744237337,
            revocation_time=0,
            revoked=False,
            is_offchain=True,
        ),
        # Owner project
        LabelsDecoded(
            id="0xdef4567890abcdef1234567890abcdef1234567890abcdef1234567890abc123",
            chain_id="eip155:1",
            address="0x6B175474E89094C44Da98b954EedeAC495271d0F",
            tag_id="owner_project",
            tag_value="makerdao",
            attester="0xA725646c05e6Bb813d98C5aBB4E72DF4bcF00B56",
            time_created=1744237337,
            revocation_time=0,
            revoked=False,
            is_offchain=True,
        ),
        # Revoked label
        LabelsDecoded(
            id="0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef",
            chain_id="eip155:1",
            address="0x742d35Cc6634C0532925a3b844Bc454e4438f44e",
            tag_id="is_eoa",
            tag_value="true",
            attester="0xA725646c05e6Bb813d98C5aBB4E72DF4bcF00B56",
            time_created=1744237337,
            revocation_time=1744237338,
            revoked=True,
            is_offchain=True,
        ),
        LabelsDecoded(
            id="0xd16d9ca932c3263c17df8a2b7618fde52b66e8194287a06de0cf205dc49e6bcf",
            chain_id="eip155:1",
            address="0x6b175474e89094c44da98b954eedeac495271d0f",
            tag_id="usage_category",
            tag_value="stablecoin",
            attester="0xa725646c05e6bb813d98c5abb4e72df4bcf00b56",
            time_created=1744237337,
            revocation_time=0,
            revoked=False,
            is_offchain=True,
        ),
    ],
)
