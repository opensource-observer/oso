from datetime import date
from typing import List, Optional

from metrics_tools.seed.types import Column, SeedConfig
from pydantic import BaseModel


class IndexedArgElement(BaseModel):
    element: str | None = Column("VARCHAR")


class IndexedArgs(BaseModel):
    list: List[IndexedArgElement] | None = Column("ARRAY(ROW(?))")


class Logs(BaseModel):
    network: Optional[str] = Column("VARCHAR")
    chain_id: Optional[int] = Column("BIGINT")
    block_timestamp: Optional[int] = Column("BIGINT")
    block_number: Optional[int] = Column("BIGINT")
    block_hash: Optional[str] = Column("VARCHAR")
    transaction_hash: Optional[str] = Column("VARCHAR")
    transaction_index: Optional[int] = Column("BIGINT")
    log_index: Optional[int] = Column("BIGINT")
    address: Optional[str] = Column("VARCHAR")
    topics: Optional[str] = Column("VARCHAR")
    data: Optional[str] = Column("VARCHAR")
    topic0: Optional[str] = Column("VARCHAR")
    indexed_args: Optional[IndexedArgs] = Column("ROW(?)")
    chain: Optional[str] = Column("VARCHAR")
    dt: Optional[date] = Column("DATE")


seed = SeedConfig(
    catalog="bigquery",
    schema="optimism_superchain_raw_onchain_data",
    table="logs",
    base=Logs,
    rows=[
        Logs(
            network="mainnet",
            chain_id=480,
            block_timestamp=1744714165,
            block_number=12689263,
            block_hash="0x…102e",
            transaction_hash="0x…2618",
            transaction_index=1,
            log_index=0,
            address="0x57b930…e0330d",
            topics="0xff…964e,0x00…3f46c",
            data="0x…68dbb5b5",
            topic0="0xff…964e",
            indexed_args=IndexedArgs(
                list=[
                    IndexedArgElement(
                        element="0x00000000000000000000000025d02783c562cbdcfa6eba07f7478b9332d3f46c"
                    )
                ]
            ),
            chain="worldchain",
            dt=date.fromisoformat("2025-04-15"),
        ),
        Logs(
            network="mainnet",
            chain_id=480,
            block_timestamp=1744704135,
            block_number=12684248,
            block_hash="0x63db13d5f2adf7c3227ccb30b51f0df46215b7ced362be389c8c81406c4eabed",
            transaction_hash="0x3026a28bfe3f81b14553686d46d2d98f9a2bb391905564834ffad39c969627d0",
            transaction_index=1,
            log_index=0,
            address="0x57b930d551e677cc36e2fa036ae2fe8fdae0330d",
            topics="0xff3030c6130ceef62c6e2035eff94706ab44e8d46a7acc3135c720ee3fac964e,0x00000000000000000000000052524776e9906ea3cad0930c29053a986e22a10a",
            data="0x0000000000000000000000000000000000000000000000000000000068db8e87",
            topic0="0xff3030c6130ceef62c6e2035eff94706ab44e8d46a7acc3135c720ee3fac964e",
            indexed_args=IndexedArgs(
                list=[
                    IndexedArgElement(
                        element="0x00000000000000000000000052524776e9906ea3cad0930c29053a986e22a10a"
                    )
                ]
            ),
            chain="worldchain",
            dt=date.fromisoformat("2025-04-15"),
        ),
    ],
)
