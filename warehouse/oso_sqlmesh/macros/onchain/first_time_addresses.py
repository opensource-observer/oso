from metrics_tools.utils.glot import coerce_to_column
from sqlglot import expressions as exp
from sqlmesh import macro
from sqlmesh.core.macros import MacroEvaluator


@macro()
def first_time_addresses(
    evaluator: MacroEvaluator,
    start: exp.Expression,
    end: exp.Expression,
    transactions_table: exp.Expression,
    *additional_column_defs: exp.ExpOrStr,
    chain_name_column: exp.ExpOrStr = "transactions.chain",
    block_timestamp_column: exp.ExpOrStr = "transactions.block_timestamp",
    block_number_column: exp.ExpOrStr = "transactions.block_number",
    from_address_column: exp.ExpOrStr = "transactions.from_address",
    to_address_column: exp.ExpOrStr = "transactions.to_address",
    hash_column: exp.ExpOrStr = "transactions.hash",
    input_column: exp.ExpOrStr = "transactions.input",
    gas_price_column: exp.ExpOrStr = "transactions.gas_price",
    receipt_status_column: exp.ExpOrStr = "transactions.receipt_status",
    receipt_gas_used_column: exp.ExpOrStr = "transactions.receipt_gas_used",
    time_partition_column: exp.ExpOrStr = "transactions.block_timestamp",
) -> exp.Expression:
    """
    # todo:
    # 1. add first funded by
    # 2. most funded by
    """
    chain_name = coerce_to_column(chain_name_column)
    chain_name_lower = exp.Lower(this=chain_name)
    block_timestamp = coerce_to_column(block_timestamp_column)
    block_number = coerce_to_column(block_number_column)
    from_address = coerce_to_column(from_address_column)
    to_address = coerce_to_column(to_address_column)
    hash = coerce_to_column(hash_column)
    input = coerce_to_column(input_column)
    gas_price = coerce_to_column(gas_price_column)
    receipt_status = coerce_to_column(receipt_status_column)
    receipt_gas_used = coerce_to_column(receipt_gas_used_column)
    time_partition = coerce_to_column(time_partition_column)

    transactions_cte = (
        exp.select(
            from_address.as_("address"),
            chain_name_lower.as_("chain_name"),
            exp.Min(this=block_timestamp).as_("first_block_timestamp"),
            exp.Min(this=block_number).as_("first_block_number"),
            exp.ArgMin(this=from_address, expression=block_number).as_("first_tx_from"),
            exp.ArgMin(this=to_address, expression=block_number).as_("first_tx_to"),
            exp.ArgMin(this=hash, expression=block_number).as_("first_tx_hash"),
            exp.ArgMin(this=exp.Substring(this=input, start=exp.Literal.number(1), length=exp.Literal.number(10)), expression=block_number).as_("first_method_id"),
            *additional_column_defs,
        )
        .from_(transactions_table.as_("transactions"))
        .where(exp.GT(this=gas_price, expression=exp.Literal.number(0)))
        .where(exp.EQ(this=receipt_status, expression=exp.Literal.number(1)))
        .where(exp.GT(this=receipt_gas_used, expression=exp.Literal.number(0)))
        .where(exp.Between(this=time_partition, low=start, high=end))
        .group_by(from_address, chain_name)
    )

    return (
        exp.select(
            exp.to_column("address"),
            exp.to_column("chain_name"),
            exp.to_column("first_block_timestamp"),
            exp.DateTrunc(this=exp.to_column("first_block_timestamp"), unit=exp.Literal.string("day")).as_("first_active_day"),
            exp.DateTrunc(this=exp.to_column("first_block_timestamp"), unit=exp.Literal.string("month")).as_("month_cohort"),
            exp.to_column("first_block_number"),
            exp.to_column("first_tx_to"),
            exp.to_column("first_tx_hash"),
            exp.to_column("first_method_id"),
            *additional_column_defs,
        )
        .with_("transactions_cte", as_=transactions_cte)
        .from_(exp.to_table("transactions_cte").as_("transactions"))
        #.from_(transactions_cte)
    )