from datetime import date, timedelta

from metrics_tools.seed.types import Column, SeedConfig
from pydantic import BaseModel


class Traces(BaseModel):
    network: str | None = Column("VARCHAR")
    chain_id: int | None = Column("BIGINT")
    block_timestamp: int | None = Column("BIGINT")
    block_number: int | None = Column("BIGINT")
    block_hash: str | None = Column("VARCHAR")
    transaction_hash: str | None = Column("VARCHAR")
    transaction_index: int | None = Column("BIGINT")
    from_address: str | None = Column("VARCHAR")
    to_address: str | None = Column("VARCHAR")
    value_64: int | None = Column("BIGINT")
    value_lossless: str | None = Column("VARCHAR")
    input: str | None = Column("VARCHAR")
    output: str | None = Column("VARCHAR")
    trace_type: str | None = Column("VARCHAR")
    call_type: str | None = Column("VARCHAR")
    reward_type: str | None = Column("VARCHAR")
    gas: int | None = Column("BIGINT")
    gas_used: int | None = Column("BIGINT")
    subtraces: int | None = Column("BIGINT")
    trace_address: str | None = Column("VARCHAR")
    error: str | None = Column("VARCHAR")
    status: int | None = Column("BIGINT")
    chain: str | None = Column("VARCHAR")
    dt: date | None = Column("DATE")


seed = SeedConfig(
    catalog="bigquery",
    schema="optimism_superchain_raw_onchain_data",
    table="traces",
    base=Traces,
    rows=[
        Traces(
            network="network1",
            chain_id=1,
            block_timestamp=1622547800,
            block_number=123456,
            block_hash="block_hash1",
            transaction_hash="tx_hash1",
            transaction_index=1,
            from_address="from_address1",
            to_address="to_address1",
            value_64=1,
            value_lossless="value_lossless1",
            input="input1",
            output="output1",
            trace_type="trace_type1",
            call_type="call_type1",
            reward_type="reward_type1",
            gas=21000,
            gas_used=20000,
            subtraces=1,
            trace_address="trace_address1",
            error="error1",
            status=1,
            chain="chain1",
            dt=date.today() - timedelta(days=1),
        ),
        Traces(
            network="network2",
            chain_id=2,
            block_timestamp=1622547801,
            block_number=123457,
            block_hash="block_hash2",
            transaction_hash="tx_hash2",
            transaction_index=2,
            from_address="from_address2",
            to_address="to_address2",
            value_64=2,
            value_lossless="value_lossless2",
            input="input2",
            output="output2",
            trace_type="trace_type2",
            call_type="call_type2",
            reward_type="reward_type2",
            gas=22000,
            gas_used=21000,
            subtraces=2,
            trace_address="trace_address2",
            error="error2",
            status=2,
            chain="chain2",
            dt=date.today(),
        ),
    ],
)
