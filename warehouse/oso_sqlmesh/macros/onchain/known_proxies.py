from metrics_tools.utils.glot import (
    coerce_to_column,
    coerce_to_table,
    literal_or_expression,
)
from sqlglot import expressions as exp
from sqlmesh import macro
from sqlmesh.core.macros import MacroEvaluator


@macro()
def known_proxies(
    evaluator: MacroEvaluator,
    start: exp.Expression,
    end: exp.Expression,
    traces_table: exp.ExpOrStr,
    *additional_column_defs: exp.ExpOrStr,
    block_timestamp_column: exp.ExpOrStr = "traces.block_timestamp",
    transaction_hash_column: exp.ExpOrStr = "traces.transaction_hash",
    from_address_column: exp.ExpOrStr = "traces.from_address",
    to_address_column: exp.ExpOrStr = "traces.to_address",
    proxy_type_column: exp.ExpOrStr = "proxies.proxy_type",
    status_column: exp.ExpOrStr = "traces.status",
    trace_type_column: exp.ExpOrStr = "traces.trace_type",
    call_type_column: exp.ExpOrStr = "traces.call_type",
    trace_type_value: exp.ExpOrStr = "call",
    call_type_value: exp.ExpOrStr = "staticcall",
    factory_address_column: exp.ExpOrStr = "proxies.factory_address",
    proxy_contracts_table: exp.ExpOrStr = "oso.seed_known_proxy_contracts",
    time_partition_column: exp.ExpOrStr = "traces.block_timestamp",
):
    traces = coerce_to_table(traces_table)
    block_timestamp = coerce_to_column(block_timestamp_column)
    transaction_hash = coerce_to_column(transaction_hash_column)
    from_address = coerce_to_column(from_address_column)
    to_address = coerce_to_column(to_address_column)
    proxy_type = coerce_to_column(proxy_type_column)
    factory_address = coerce_to_column(factory_address_column)
    proxy_contracts = coerce_to_table(proxy_contracts_table)
    trace_type = coerce_to_column(trace_type_column)
    call_type = coerce_to_column(call_type_column)
    status = coerce_to_column(status_column)
    trace_type_value_exp = literal_or_expression(trace_type_value)
    call_type_value_exp = literal_or_expression(call_type_value)
    time_partition = coerce_to_column(time_partition_column)

    proxy_address = exp.Case(
        ifs=[
            exp.If(
                this=exp.EQ(
                    this=exp.Lower(this=from_address),
                    expression=exp.Lower(this=factory_address),
                ),
                true=from_address,
            ),
            exp.If(
                this=exp.EQ(
                    this=exp.Lower(this=to_address),
                    expression=exp.Lower(this=factory_address),
                ),
                true=to_address,
            ),
        ],
        default=exp.Null(),
    )

    proxies = (
        exp.select(
            block_timestamp.as_("block_timestamp"),
            transaction_hash.as_("transaction_hash"),
            from_address.as_("from_address"),
            to_address.as_("to_address"),
            proxy_type.as_("proxy_type"),
            proxy_address.as_("proxy_address"),
            *additional_column_defs,
        )
        .from_(traces.as_("traces"))
        .join(
            proxy_contracts.as_("proxies"),
            on=exp.Or(
                this=exp.EQ(
                    this=exp.Lower(this=from_address),
                    expression=exp.Lower(this=factory_address),
                ),
                expression=exp.EQ(
                    this=exp.Lower(this=to_address),
                    expression=exp.Lower(this=factory_address),
                ),
            ),
            join_type="inner",
        )
        .where(exp.EQ(this=status, expression=exp.Literal(this="1", is_string=False)))
        .where(exp.EQ(this=call_type, expression=call_type_value_exp))
        .where(exp.EQ(this=trace_type, expression=trace_type_value_exp))
        .where(exp.NEQ(this=from_address, expression=to_address))
        .where(
            exp.Between(
                this=time_partition,
                low=start,
                high=end,
            )
        )
    )
    return proxies
