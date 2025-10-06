from datetime import datetime
from typing import Optional
from pydantic import BaseModel
from metrics_tools.seed.types import Column, SeedConfig

class Addresses(BaseModel):
    createdAt: datetime | None = Column("TIMESTAMP(6) WITH TIME ZONE")
    updatedAt: datetime | None = Column("TIMESTAMP(6) WITH TIME ZONE")
    address: bytes | None = Column("BYTEA")
    bytecode: bytes | None = Column("BYTEA")
    createdInBlockNumber: int | None = Column("BIGINT")
    creatorTxHash: bytes | None = Column("BYTEA")
    creatorAddress: bytes | None = Column("BYTEA")
    createdInLogIndex: int | None = Column("INTEGER")
    isEVMLike: bool | None = Column("BOOLEAN")

seed = SeedConfig(
    catalog="bigquery",
    schema="lens_chain_mainnet",
    table="addresses",
    base=Addresses,
    rows=[
        Addresses(
            createdAt=datetime(2025, 8, 12, 0, 4, 14, 496700),
            updatedAt=datetime(2025, 8, 12, 0, 4, 14, 496700),
            address=bytes.fromhex('ec931ead0a38ed7aa85c696334225262755c98a5'),
            bytecode=bytes.fromhex('0001000000000002001200000000000200000000000103550000006003100270'),  # Truncated for brevity
            createdInBlockNumber=3851064,
            creatorTxHash=bytes.fromhex('ce71f83100d221ea8fa64f08f8fd7ce3536153b9f4096d13e66dbd62cb28ab4f'),
            creatorAddress=bytes.fromhex('802080d804d93279e257dabbb2d090c4ff0ebdbe'),
            createdInLogIndex=12,
            isEVMLike=False
        ),
        Addresses(
            createdAt=datetime(2025, 8, 12, 0, 4, 37, 100273),
            updatedAt=datetime(2025, 8, 12, 0, 4, 37, 100273),
            address=bytes.fromhex('c15cbfc77a83736cb78b170d40e6037abd434777'),
            bytecode=bytes.fromhex('0001000000000002001200000000000200000000000103550000006003100270'),  # Truncated for brevity
            createdInBlockNumber=3851065,
            creatorTxHash=bytes.fromhex('b8c0b470edbdc3ae32ef5916fd3f32a1905beeee956a08d0999237d3687fa7a9'),
            creatorAddress=bytes.fromhex('802080d804d93279e257dabbb2d090c4ff0ebdbe'),
            createdInLogIndex=12,
            isEVMLike=False
        )
    ]
)