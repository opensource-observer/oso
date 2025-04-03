from datetime import date, timedelta

from metrics_tools.seed.loader import DestinationLoader
from metrics_tools.seed.types import Column
from pydantic import BaseModel


class Transactions(BaseModel):
    network: str | None = Column("VARCHAR")
    chain_id: int | None = Column("BIGINT")
    block_timestamp: int | None = Column("BIGINT")
    block_number: int | None = Column("BIGINT")
    block_hash: str | None = Column("VARCHAR")
    hash: str | None = Column("VARCHAR")
    nonce: int | None = Column("BIGINT")
    transaction_index: int | None = Column("BIGINT")
    from_address: str | None = Column("VARCHAR")
    to_address: str | None = Column("VARCHAR")
    value_64: int | None = Column("BIGINT")
    value_lossless: str | None = Column("VARCHAR")
    gas: int | None = Column("BIGINT")
    gas_price: int | None = Column("BIGINT")
    input: str | None = Column("VARCHAR")
    transaction_type: int | None = Column("BIGINT")
    max_fee_per_gas: int | None = Column("BIGINT")
    max_priority_fee_per_gas: int | None = Column("BIGINT")
    receipt_cumulative_gas_used: int | None = Column("BIGINT")
    receipt_gas_used: int | None = Column("BIGINT")
    receipt_contract_address: str | None = Column("VARCHAR")
    receipt_status: int | None = Column("BIGINT")
    receipt_effective_gas_price: int | None = Column("BIGINT")
    receipt_l1_gas_price: int | None = Column("BIGINT")
    receipt_l1_gas_used: int | None = Column("BIGINT")
    receipt_l1_fee: int | None = Column("BIGINT")
    receipt_l1_fee_scalar: float | None = Column("DOUBLE")
    receipt_l1_blob_base_fee: int | None = Column("BIGINT")
    receipt_l1_blob_base_fee_scalar: int | None = Column("BIGINT")
    receipt_l1_base_fee_scalar: int | None = Column("BIGINT")
    chain: str | None = Column("VARCHAR")
    dt: date | None = Column("DATE")


async def seed(loader: DestinationLoader):
    await loader.create_table(
        "optimism_superchain_raw_onchain_data.transactions", Transactions
    )

    await loader.insert(
        "optimism_superchain_raw_onchain_data.transactions",
        [
            Transactions(
                network="network1",
                chain_id=1,
                block_timestamp=1622547800,
                block_number=123456,
                block_hash="block_hash1",
                hash="hash1",
                nonce=1,
                transaction_index=1,
                from_address="from_address1",
                to_address="to_address1",
                value_64=1,
                value_lossless="value_lossless1",
                gas=21000,
                gas_price=1,
                input="input1",
                transaction_type=1,
                max_fee_per_gas=1,
                max_priority_fee_per_gas=1,
                receipt_cumulative_gas_used=1,
                receipt_gas_used=1,
                receipt_contract_address="receipt_contract_address1",
                receipt_status=1,
                receipt_effective_gas_price=1,
                receipt_l1_gas_price=1,
                receipt_l1_gas_used=1,
                receipt_l1_fee=1,
                receipt_l1_fee_scalar=1.0,
                receipt_l1_blob_base_fee=1,
                receipt_l1_blob_base_fee_scalar=1,
                receipt_l1_base_fee_scalar=1,
                chain="chain1",
                dt=date.today() - timedelta(days=1),
            ),
            Transactions(
                network="network2",
                chain_id=2,
                block_timestamp=1622547801,
                block_number=123457,
                block_hash="block_hash2",
                hash="hash2",
                nonce=2,
                transaction_index=2,
                from_address="from_address2",
                to_address="to_address2",
                value_64=2,
                value_lossless="value_lossless2",
                gas=22000,
                gas_price=2,
                input="input2",
                transaction_type=2,
                max_fee_per_gas=2,
                max_priority_fee_per_gas=2,
                receipt_cumulative_gas_used=2,
                receipt_gas_used=2,
                receipt_contract_address="receipt_contract_address2",
                receipt_status=2,
                receipt_effective_gas_price=2,
                receipt_l1_gas_price=2,
                receipt_l1_gas_used=2,
                receipt_l1_fee=2,
                receipt_l1_fee_scalar=2.0,
                receipt_l1_blob_base_fee=2,
                receipt_l1_blob_base_fee_scalar=2,
                receipt_l1_base_fee_scalar=2,
                chain="chain2",
                dt=date.today(),
            ),
        ],
    )
