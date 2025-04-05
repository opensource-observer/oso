from datetime import date, timedelta

from metrics_tools.seed.types import Column, SeedConfig
from pydantic import BaseModel


class UserOperationEventLogsV2(BaseModel):
    chain_id: int | None = Column("BIGINT")
    network: str | None = Column("VARCHAR")
    block_timestamp: int | None = Column("BIGINT")
    block_number: int | None = Column("BIGINT")
    block_hash: str | None = Column("VARCHAR")
    transaction_hash: str | None = Column("VARCHAR")
    transaction_index: int | None = Column("BIGINT")
    log_index: int | None = Column("BIGINT")
    contract_address: str | None = Column("VARCHAR")
    userophash: str | None = Column("VARCHAR")
    sender: str | None = Column("VARCHAR")
    paymaster: str | None = Column("VARCHAR")
    nonce: str | None = Column("VARCHAR")
    success: bool | None = Column("BOOLEAN")
    actualgascost: str | None = Column("VARCHAR")
    actualgasused: str | None = Column("VARCHAR")
    chain: str | None = Column("VARCHAR")
    dt: date | None = Column("DATE")


seed = SeedConfig(
    catalog="bigquery",
    schema="optimism_superchain_4337_account_abstraction_data",
    table="useroperationevent_logs_v2",
    base=UserOperationEventLogsV2,
    rows=[
        UserOperationEventLogsV2(
            chain_id=1,
            network="network1",
            block_timestamp=1622547800,
            block_number=123456,
            block_hash="block_hash1",
            transaction_hash="tx_hash1",
            transaction_index=1,
            log_index=1,
            contract_address="contract_address1",
            userophash="userophash1",
            sender="sender1",
            paymaster="paymaster1",
            nonce="nonce1",
            success=True,
            actualgascost="actualgascost1",
            actualgasused="actualgasused1",
            chain="chain1",
            dt=date.today() - timedelta(days=1),
        ),
        UserOperationEventLogsV2(
            chain_id=2,
            network="network2",
            block_timestamp=1622547801,
            block_number=123457,
            block_hash="block_hash2",
            transaction_hash="tx_hash2",
            transaction_index=2,
            log_index=2,
            contract_address="contract_address2",
            userophash="userophash2",
            sender="sender2",
            paymaster="paymaster2",
            nonce="nonce2",
            success=False,
            actualgascost="actualgascost2",
            actualgasused="actualgasused2",
            chain="chain2",
            dt=date.today(),
        ),
    ],
)
