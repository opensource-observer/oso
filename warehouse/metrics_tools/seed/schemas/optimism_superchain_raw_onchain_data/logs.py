from datetime import date
from typing import List, Optional

from metrics_tools.seed.types import Column, SeedConfig
from pydantic import BaseModel


class IndexedArgElement(BaseModel):
    element: Optional[str] = Column("VARCHAR")


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
            chain_id=8453,
            block_timestamp=1743518845,
            block_number=28364749,
            block_hash="0x26ee7f05b05e5bf19b646c9066b3a648b9aafa31f7febaed3c76d30e9c6d45be",
            transaction_hash="0xe42816f15ecd0ad41d410049bc7edd3e0916c51b377e621ea7aa38601c09ca19",
            transaction_index=1,
            log_index=0,
            address="0x4e962bb3889bf030368f56810a9c96b83cb3e778",
            topics=(
                "0x0c396cd989a39f4459b5fa1aed6a9a8dcdbc45908acfd67e028cd568da"
                "98982c,0x0000000000000000000000006399ed6725cc163d019aa64ff55b2214"
                "9d7179a8,0xfffffffffffffffffffffffffffffffffffffffffffffffffffef9"
                "1c,0xfffffffffffffffffffffffffffffffffffffffffffffffffffef980"
            ),
            data="0x" + "0" * 192,
            topic0="0x0c396cd989a39f4459b5fa1aed6a9a8dcdbc45908acfd67e028cd568da98982c",
            indexed_args=IndexedArgs(
                list=[
                    IndexedArgElement(element="0x0000000000000000000000006399ed6725cc163d019aa64ff55b22149d7179a8"),
                    IndexedArgElement(element="0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffef91c"),
                    IndexedArgElement(element="0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffef980"),
                ]
            ),
            chain="base",
            dt=date.fromisoformat("2025-04-01"),
        ),
        Logs(
            network="mainnet",
            chain_id=8453,
            block_timestamp=1743481207,
            block_number=28345930,
            block_hash="0x1862884f55e020acea492dc01a84f30e951ba6127953326437860405dcbcf0c8",
            transaction_hash="0xf398d0dcbc3f5c452e3faad38c07fd1b62e8af4e5789db3f88138451f6f42ba3",
            transaction_index=1,
            log_index=9,
            address="0xb5f0b4ae66c14f7efaa9aa1468e8fc536a3e288c",
            topics=(
                "0x0c396cd989a39f4459b5fa1aed6a9a8dcdbc45908acfd67e028cd568da"
                "98982c,0x000000000000000000000000827922686190790b37229fd06084350e"
                "74485b72,0x00000000000000000000000000000000000000000000000000000000"
                "00011d28,0x00000000000000000000000000000000000000000000000000000000"
                "00011df0"
            ),
            data=(
                "0x000000000000000000000000000000000000000000000d6702429f1b4f5"
                "d97e10000000000000000000000000000000000000000000000009ed9e7"
                "ad8bd24cff00000000000000000000000000000000000000000000018c2"
                "97777547af9ef0d"
            ),
            topic0="0x0c396cd989a39f4459b5fa1aed6a9a8dcdbc45908acfd67e028cd568da98982c",
            indexed_args=IndexedArgs(
                list=[
                    IndexedArgElement(element="0x000000000000000000000000827922686190790b37229fd06084350e74485b72"),
                    IndexedArgElement(element="0x00000000000000000000000000000000000000000000000000000000000011d28"),
                    IndexedArgElement(element="0x00000000000000000000000000000000000000000000000000000000000011df0"),
                ]
            ),
            chain="base",
            dt=date.fromisoformat("2025-04-01"),
        ),
        Logs(
            network="mainnet",
            chain_id=480,
            block_timestamp=1744714165,
            block_number=12689263,
            block_hash="0xccd0c51cfa41a1baf3cbfc61c26d63bcd48fc86cc7d7cdc8fce9fe59faf4102e",
            transaction_hash="0xa6b386f8f9e695b4eb414bf0a5f6415257161c637cfad1fba83d33e3c1a2d618",
            transaction_index=1,
            log_index=0,
            address="0x57b930d551e677cc36e2fa036ae2fe8fdae0330d",
            topics="0xff3030c6130ceef62c6e2035eff94706ab44e8d46a7acc3135c720ee3fac964e,0x00000000000000000000000025d02783c562cbdcfa6eba07f7478b9332d3f46c",
            data="0x0000000000000000000000000000000000000000000000000000000068dbb5b5",
            topic0="0xff3030c6130ceef62c6e2035eff94706ab44e8d46a7acc3135c720ee3fac964e",
            indexed_args=IndexedArgs(
                list=[
                    IndexedArgElement(element="0x00000000000000000000000025d02783c562cbdcfa6eba07f7478b9332d3f46c")
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
                    IndexedArgElement(element="0x00000000000000000000000052524776e9906ea3cad0930c29053a986e22a10a")
                ]
            ),
            chain="worldchain",
            dt=date.fromisoformat("2025-04-15"),
        ),
    ],
)
