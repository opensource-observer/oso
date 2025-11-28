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
            dt=date.today(),
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
            dt=date.today(),
        ),
        Logs(
            network="mainnet",
            chain_id=130,
            block_timestamp=1763334773,
            block_number=32586414,
            block_hash="0x882e9d4a5b2bfc2f619b61a81cfd8c788ded184c91c395070bb6e3cdc74c45d3",
            transaction_hash="0xd7b4e87e4002aa690dc22443d79a2ac7c3ccb1999d1f9afd06077d29da81ac4f",
            transaction_index=8,
            log_index=86,
            address="0x22c1f6050e56d2876009903609a2cc3fef83b415",
            topics="0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef,0x0000000000000000000000000000000000000000000000000000000000000000,0x000000000000000000000000abbe765847c1ad0650f420dbe6686f758d26189d,0x0000000000000000000000000000000000000000000000000000000000726756",
            data="0x",
            topic0="0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef",
            indexed_args=IndexedArgs(
                list=[
                    IndexedArgElement(
                        element="0x0000000000000000000000000000000000000000000000000000000000000000"
                    ),
                    IndexedArgElement(
                        element="0x000000000000000000000000abbe765847c1ad0650f420dbe6686f758d26189d"
                    ),
                    IndexedArgElement(
                        element="0x0000000000000000000000000000000000000000000000000000000000726756"
                    ),
                ]
            ),
            chain="unichain",
            dt=date.today(),
        ),
    ],
)
