from datetime import datetime
from typing import Optional
from pydantic import BaseModel
from metrics_tools.seed.types import Column, SeedConfig

class Blocks(BaseModel):
    createdAt: datetime | None = Column("TIMESTAMP(6) WITH TIME ZONE")
    updatedAt: datetime | None = Column("TIMESTAMP(6) WITH TIME ZONE")
    number: int | None = Column("BIGINT")
    nonce: str | None = Column("VARCHAR")
    difficulty: int | None = Column("INTEGER")
    gasLimit: str | None = Column("VARCHAR(128)")
    gasUsed: str | None = Column("VARCHAR(128)")
    baseFeePerGas: str | None = Column("VARCHAR(128)")
    l1BatchNumber: int | None = Column("BIGINT")
    l1TxCount: int | None = Column("INTEGER")
    l2TxCount: int | None = Column("INTEGER")
    hash: bytes | None = Column("BYTEA")
    parentHash: bytes | None = Column("BYTEA")
    miner: bytes | None = Column("BYTEA")
    extraData: Optional[bytes] = Column("BYTEA")
    timestamp: datetime | None = Column("TIMESTAMP(6) WITH TIME ZONE")

seed = SeedConfig(
    catalog="bigquery",
    schema="lens_chain_mainnet",
    table="blocks",
    base=Blocks,
    rows=[
        Blocks(
            createdAt=datetime(2025, 8, 28, 2, 41, 46, 182096),
            updatedAt=datetime(2025, 8, 28, 2, 41, 46, 182096),
            number=4129986,
            nonce="0x0000000000000000",
            difficulty=0,
            gasLimit="1125899906842624",
            gasUsed="0",
            baseFeePerGas="2771543782",
            l1BatchNumber=7598,
            l1TxCount=0,
            l2TxCount=0,
            hash=bytes.fromhex("eef275000c23e5eb625f00eb4c0f10fc9df3ceb3196a"),  # truncated
            parentHash=bytes.fromhex("3ce5248f98b9503e73565268a47520f937c3b90c7146"),  # truncated
            miner=bytes.fromhex("0000000000000000000000000000000000000000"),
            extraData=None,
            timestamp=datetime(2025, 8, 28, 2, 41, 24)
        ),
        Blocks(
            createdAt=datetime(2025, 8, 28, 5, 59, 29, 217390),
            updatedAt=datetime(2025, 8, 28, 5, 59, 29, 217390),
            number=4131874,
            nonce="0x0000000000000000",
            difficulty=0,
            gasLimit="1125899906842624",
            gasUsed="0",
            baseFeePerGas="2771305326",
            l1BatchNumber=7599,
            l1TxCount=0,
            l2TxCount=0,
            hash=bytes.fromhex("8183c52cd2712338bc78fb7ab3d2dac8d5bf8c2d7688"),  # truncated
            parentHash=bytes.fromhex("ba76a6b6039bd734a434135e2207c5761806a9808d96"),  # truncated
            miner=bytes.fromhex("0000000000000000000000000000000000000000"),
            extraData=None,
            timestamp=datetime(2025, 8, 28, 5, 59, 6)
        )
    ]
)
