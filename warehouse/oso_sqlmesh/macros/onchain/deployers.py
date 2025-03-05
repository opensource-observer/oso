from metrics_tools.utils.glot import coerce_to_column
from sqlglot import expressions as exp
from sqlmesh import macro
from sqlmesh.core.macros import MacroEvaluator


@macro()
def transactions_with_receipts_deployers(
    evaluator: MacroEvaluator,
    start: exp.Expression,
    end: exp.Expression,
    transactions_table: exp.Expression,
    *additional_column_defs: exp.ExpOrStr,
    block_timestamp_column: exp.ExpOrStr = "transactions.block_timestamp",
    transaction_hash_column: exp.ExpOrStr = "transactions.hash",
    deployer_address_column: exp.ExpOrStr = "transactions.from_address",
    contract_address_column: exp.ExpOrStr = "transactions.receipt_contract_address",
    to_address_column: exp.ExpOrStr = "transactions.to_address",
    receipt_status_column: exp.ExpOrStr = "transactions.receipt_status",
    time_partition_column: exp.ExpOrStr = "transactions.block_timestamp",
) -> exp.Expression:
    """Get the SQL for the transactions_with_receipts_deployers macro."""
    block_timestamp = coerce_to_column(block_timestamp_column)
    transaction_hash = coerce_to_column(transaction_hash_column)
    deployer_address = coerce_to_column(deployer_address_column)
    contract_address = coerce_to_column(contract_address_column)
    to_address = coerce_to_column(to_address_column)
    receipt_status = coerce_to_column(receipt_status_column)
    time_partition = coerce_to_column(time_partition_column)

    return (
        exp.select(
            block_timestamp.as_("block_timestamp"),
            transaction_hash.as_("transaction_hash"),
            deployer_address.as_("deployer_address"),
            contract_address.as_("contract_address"),
            *additional_column_defs,
        )
        .from_(transactions_table.as_("transactions"))
        .where(
            exp.Or(
                this=exp.Is(this=to_address, expression=exp.Null()),
                expression=exp.EQ(this=to_address, expression=exp.Literal.string("")),
            )
        )
        .where(
            exp.EQ(
                this=receipt_status, expression=exp.Literal(this="1", is_string=False)
            )
        )
        .where(
            exp.Between(
                this=time_partition,
                low=start,
                high=end,
            )
        )
    )
