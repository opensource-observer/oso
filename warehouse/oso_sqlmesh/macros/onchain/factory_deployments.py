from metrics_tools.utils.glot import coerce_to_column
from sqlglot import expressions as exp
from sqlmesh import macro
from sqlmesh.core.macros import MacroEvaluator


@macro()
def factory_deployments(
    evaluator: MacroEvaluator,
    start: exp.Expression,
    end: exp.Expression,
    transactions_table: exp.Expression,
    traces_tables: exp.Expression,
    *additional_column_defs: exp.ExpOrStr,
    transactions_transaction_hash_column: exp.ExpOrStr = "transactions.hash",
    transactions_originating_address_column: exp.ExpOrStr = "transactions.from_address",
    transactions_originating_contract_column: exp.ExpOrStr = "transactions.to_address",
    transactions_time_partition_column: exp.ExpOrStr = "transactions.block_timestamp",
    traces_transaction_hash_column: exp.ExpOrStr = "traces.transaction_hash",
    traces_block_timestamp_column: exp.ExpOrStr = "traces.block_timestamp",
    traces_factory_address_column: exp.ExpOrStr = "traces.from_address",
    traces_contract_address_column: exp.ExpOrStr = "traces.to_address",
    traces_trace_type_column: exp.ExpOrStr = "traces.trace_type",
    traces_status_column: exp.ExpOrStr = "traces.status",
    traces_time_partition_column: exp.ExpOrStr = "traces.block_timestamp",
) -> exp.Expression:
    """Get the SQL for the transactions_with_receipts_deployers macro.

    This macro generates a sql query that retrieves factory deployments from the
    transactions and traces tables within a specified time range. It filters for
    'create' and 'create2' trace types, excludes a the create2 EOA
    0x3fab184622dc19b6109349b94811493bf2a45362 see:

    https://github.com/Arachnid/deterministic-deployment-proxy
    
    Args:
        evaluator (MacroEvaluator): The macro evaluator instance.
        start (exp.Expression): The start of the time range for filtering.
        end (exp.Expression): The end of the time range for filtering.
        transactions_table (exp.Expression): The transactions table expression.
        traces_tables (exp.Expression): The traces table expression.
        additional_column_defs (exp.ExpOrStr): Additional column definitions to include in the result.
        transactions_transaction_hash_column (exp.ExpOrStr): Column for transaction hash in the transactions table.
        transactions_originating_address_column (exp.ExpOrStr): Column for originating address in the transactions table.
        transactions_originating_contract_column (exp.ExpOrStr): Column for originating contract in the transactions table.
        transactions_time_partition_column (exp.ExpOrStr): Column for time partition in the transactions table.
        traces_transaction_hash_column (exp.ExpOrStr): Column for transaction hash in the traces table.
        traces_block_timestamp_column (exp.ExpOrStr): Column for block timestamp in the traces table.
        traces_factory_address_column (exp.ExpOrStr): Column for factory address in the traces table.
        traces_contract_address_column (exp.ExpOrStr): Column for contract address in the traces table.
        traces_trace_type_column (exp.ExpOrStr): Column for trace type in the traces table.
        traces_status_column (exp.ExpOrStr): Column for trace status in the traces table.
        traces_time_partition_column (exp.ExpOrStr): Column for time partition in the traces table.

    Returns:
        exp.Expression: The SQL expression for the factory deployments query.
            The generated results for this sql query include the following columns:

            - block_timestamp: The timestamp of the block in which the transaction was included.
            - transaction_hash: The hash of the transaction.
            - originating_address: The address that initiated the transaction
            - originating_contract: The contract address that initiated the transaction 
                if this is null then this a contract deployment by an EOA
            - factory_address: The address of the factory contract that deployed the new contract 
                if this is the same as the originating address then this is a contract deployment 
                by an EOA
            - contract_address: The address of the newly deployed contract.
            - create_type: The type of creation, either 'create' or 'create2'.
            - Finally, we append any additional columns defined in the macro call
    """
    transactions_transaction_hash = coerce_to_column(
        transactions_transaction_hash_column
    )
    transactions_time_partition = coerce_to_column(transactions_time_partition_column)

    traces_block_timestamp = coerce_to_column(traces_block_timestamp_column)
    traces_transaction_hash = coerce_to_column(traces_transaction_hash_column)
    traces_contract_address = coerce_to_column(traces_contract_address_column)
    traces_factory_address = coerce_to_column(traces_factory_address_column)
    transactions_originating_address = coerce_to_column(
        transactions_originating_address_column
    )
    transactions_originating_contract = coerce_to_column(
        transactions_originating_contract_column
    )
    traces_trace_type = coerce_to_column(traces_trace_type_column)
    traces_status = coerce_to_column(traces_status_column)
    traces_time_partition = coerce_to_column(traces_time_partition_column)

    transactions_cte = (
        exp.select("*")
        .from_(transactions_table.as_("transactions"))
        .where(
            exp.Between(
                this=transactions_time_partition,
                low=start,
                high=end,
            )
        )
    )

    return (
        exp.select(
            traces_block_timestamp.as_("block_timestamp"),
            traces_transaction_hash.as_("transaction_hash"),
            transactions_originating_address.as_("originating_address"),
            transactions_originating_contract.as_("originating_contract"),
            traces_factory_address.as_("factory_address"),
            traces_contract_address.as_("contract_address"),
            traces_trace_type.as_("create_type"),
            *additional_column_defs,
        )
        .with_("transactions_cte", as_=transactions_cte)
        .from_(traces_tables.as_("traces"))
        .join(
            exp.to_table("transactions_cte").as_("transactions"),
            on=exp.EQ(
                this=traces_transaction_hash, expression=transactions_transaction_hash
            ),
            join_type="inner",
        )
        .where(
            exp.NEQ(
                this=exp.Lower(this=traces_factory_address),
                expression=exp.Literal(
                    this="0x3fab184622dc19b6109349b94811493bf2a45362", is_string=True
                ),
            )
        )
        .where(
            exp.In(
                this=exp.Lower(this=traces_trace_type),
                expressions=[
                    exp.Literal(this="create", is_string=True),
                    exp.Literal(this="create2", is_string=True),
                ],
            )
        )
        .where(
            exp.EQ(
                this=traces_status,
                expression=exp.Literal(this="1", is_string=False),
            )
        )
        .where(
            exp.Between(
                this=traces_time_partition,
                low=start,
                high=end,
            )
        )
    )
