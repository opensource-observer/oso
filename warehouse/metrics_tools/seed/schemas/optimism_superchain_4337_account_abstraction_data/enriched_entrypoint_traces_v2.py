from datetime import date, timedelta

from metrics_tools.seed.types import Column, SeedConfig
from pydantic import BaseModel


class EnrichedEntrypointTracesV2(BaseModel):
    chain_id: int | None = Column("BIGINT")
    network: str | None = Column("VARCHAR")
    block_timestamp: int | None = Column("BIGINT")
    block_number: int | None = Column("BIGINT")
    block_hash: str | None = Column("VARCHAR")
    transaction_hash: str | None = Column("VARCHAR")
    transaction_index: int | None = Column("BIGINT")
    from_address: str | None = Column("VARCHAR")
    to_address: str | None = Column("VARCHAR")
    value: str | None = Column("VARCHAR")
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
    trace_root: int | None = Column("BIGINT")
    method_id: str | None = Column("VARCHAR")
    tx_from_address: str | None = Column("VARCHAR")
    bundler_address: str | None = Column("VARCHAR")
    entrypoint_contract_address: str | None = Column("VARCHAR")
    entrypoint_contract_version: str | None = Column("VARCHAR")
    innerhandleop_trace_address: str | None = Column("VARCHAR")
    is_innerhandleop: bool | None = Column("BOOLEAN")
    is_from_sender: bool | None = Column("BOOLEAN")
    userop_sender: str | None = Column("VARCHAR")
    userop_paymaster: str | None = Column("VARCHAR")
    userop_hash: str | None = Column("VARCHAR")
    userop_calldata: str | None = Column("VARCHAR")
    innerhandleop_decodeerror: str | None = Column("VARCHAR")
    innerhandleop_opinfo: str | None = Column("VARCHAR")
    innerhandleop_context: str | None = Column("VARCHAR")
    useropevent_nonce: str | None = Column("VARCHAR")
    useropevent_success: bool | None = Column("BOOLEAN")
    useropevent_actualgascost: str | None = Column("VARCHAR")
    useropevent_actualgasused: str | None = Column("VARCHAR")
    userop_idx: int | None = Column("BIGINT")
    useropevent_actualgascost_eth: float | None = Column("DOUBLE")
    chain: str | None = Column("VARCHAR")
    dt: date | None = Column("DATE")


seed = SeedConfig(
    catalog="bigquery",
    schema="optimism_superchain_4337_account_abstraction_data",
    table="enriched_entrypoint_traces_v2",
    base=EnrichedEntrypointTracesV2,
    rows=[
        EnrichedEntrypointTracesV2(
            chain_id=1,
            network="network1",
            block_timestamp=1622547800,
            block_number=123456,
            block_hash="block_hash1",
            transaction_hash="tx_hash1",
            transaction_index=1,
            from_address="from_address1",
            to_address="to_address1",
            value="value1",
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
            trace_root=1,
            method_id="method_id1",
            tx_from_address="tx_from_address1",
            bundler_address="bundler_address1",
            entrypoint_contract_address="entrypoint_contract_address1",
            entrypoint_contract_version="v1",
            innerhandleop_trace_address="trace_address1",
            is_innerhandleop=True,
            is_from_sender=True,
            userop_sender="userop_sender1",
            userop_paymaster="userop_paymaster1",
            userop_hash="userop_hash1",
            userop_calldata="userop_calldata1",
            innerhandleop_decodeerror="decodeerror1",
            innerhandleop_opinfo="opinfo1",
            innerhandleop_context="context1",
            useropevent_nonce="nonce1",
            useropevent_success=True,
            useropevent_actualgascost="actualgascost1",
            useropevent_actualgasused="actualgasused1",
            userop_idx=1,
            useropevent_actualgascost_eth=0.01,
            chain="chain1",
            dt=date.today() - timedelta(days=1),
        ),
        EnrichedEntrypointTracesV2(
            chain_id=2,
            network="network2",
            block_timestamp=1622547801,
            block_number=123457,
            block_hash="block_hash2",
            transaction_hash="tx_hash2",
            transaction_index=2,
            from_address="from_address2",
            to_address="to_address2",
            value="value2",
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
            trace_root=2,
            method_id="method_id2",
            tx_from_address="tx_from_address2",
            bundler_address="bundler_address2",
            entrypoint_contract_address="entrypoint_contract_address2",
            entrypoint_contract_version="v2",
            innerhandleop_trace_address="trace_address2",
            is_innerhandleop=False,
            is_from_sender=False,
            userop_sender="userop_sender2",
            userop_paymaster="userop_paymaster2",
            userop_hash="userop_hash2",
            userop_calldata="userop_calldata2",
            innerhandleop_decodeerror="decodeerror2",
            innerhandleop_opinfo="opinfo2",
            innerhandleop_context="context2",
            useropevent_nonce="nonce2",
            useropevent_success=False,
            useropevent_actualgascost="actualgascost2",
            useropevent_actualgasused="actualgasused2",
            userop_idx=2,
            useropevent_actualgascost_eth=0.02,
            chain="chain2",
            dt=date.today(),
        ),
    ],
)
