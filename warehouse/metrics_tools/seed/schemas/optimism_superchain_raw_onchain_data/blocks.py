from datetime import date, timedelta

from metrics_tools.seed.types import Column, SeedConfig
from pydantic import BaseModel


class Blocks(BaseModel):
    network: str | None = Column("VARCHAR")
    chain_id: int | None = Column("BIGINT")
    timestamp: int | None = Column("BIGINT")
    number: int | None = Column("BIGINT")
    hash: str | None = Column("VARCHAR")
    parent_hash: str | None = Column("VARCHAR")
    nonce: str | None = Column("VARCHAR")
    sha3_uncles: str | None = Column("VARCHAR")
    logs_bloom: str | None = Column("VARCHAR")
    transactions_root: str | None = Column("VARCHAR")
    state_root: str | None = Column("VARCHAR")
    receipts_root: str | None = Column("VARCHAR")
    withdrawals_root: str | None = Column("VARCHAR")
    miner: str | None = Column("VARCHAR")
    difficulty: float | None = Column("DOUBLE")
    total_difficulty: float | None = Column("DOUBLE")
    size: int | None = Column("BIGINT")
    base_fee_per_gas: int | None = Column("BIGINT")
    gas_used: int | None = Column("BIGINT")
    gas_limit: int | None = Column("BIGINT")
    extra_data: str | None = Column("VARCHAR")
    transaction_count: int | None = Column("BIGINT")
    chain: str | None = Column("VARCHAR")
    dt: date | None = Column("DATE")


seed = SeedConfig(
    catalog="bigquery",
    schema="optimism_superchain_raw_onchain_data",
    table="blocks",
    base=Blocks,
    rows=[
        Blocks(
            network="network1",
            chain_id=1,
            timestamp=1622547800,
            number=123456,
            hash="hash1",
            parent_hash="parent_hash1",
            nonce="nonce1",
            sha3_uncles="sha3_uncles1",
            logs_bloom="logs_bloom1",
            transactions_root="transactions_root1",
            state_root="state_root1",
            receipts_root="receipts_root1",
            withdrawals_root="withdrawals_root1",
            miner="miner1",
            difficulty=1.0,
            total_difficulty=1.0,
            size=1,
            base_fee_per_gas=1,
            gas_used=1,
            gas_limit=1,
            extra_data="extra_data1",
            transaction_count=1,
            chain="chain1",
            dt=date.today() - timedelta(days=1),
        ),
        Blocks(
            network="network2",
            chain_id=2,
            timestamp=1622547801,
            number=123457,
            hash="hash2",
            parent_hash="parent_hash2",
            nonce="nonce2",
            sha3_uncles="sha3_uncles2",
            logs_bloom="logs_bloom2",
            transactions_root="transactions_root2",
            state_root="state_root2",
            receipts_root="receipts_root2",
            withdrawals_root="withdrawals_root2",
            miner="miner2",
            difficulty=2.0,
            total_difficulty=2.0,
            size=2,
            base_fee_per_gas=2,
            gas_used=2,
            gas_limit=2,
            extra_data="extra_data2",
            transaction_count=2,
            chain="chain2",
            dt=date.today(),
        ),
    ],
)
