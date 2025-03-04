from metrics_tools.utils.glot import coerce_to_column
from sqlglot import expressions as exp
from sqlmesh import macro
from sqlmesh.core.macros import MacroEvaluator


@macro()
def potential_bots(
    evaluator: MacroEvaluator,
    transactions_table: exp.Expression,
    *additional_column_defs: exp.ExpOrStr,
    chain_name_column: exp.ExpOrStr = "transactions.chain",
    block_timestamp_column: exp.ExpOrStr = "transactions.block_timestamp",
    from_address_column: exp.ExpOrStr = "transactions.from_address",
    gas_price_column: exp.ExpOrStr = "transactions.gas_price",
    receipt_gas_used_column: exp.ExpOrStr = "transactions.receipt_gas_used",
    time_partition_column: exp.ExpOrStr = "transactions.block_timestamp",
) -> exp.Expression:
    """
    Identifies potential bot addresses based on transaction patterns.
    """
    chain_name = coerce_to_column(chain_name_column)
    chain_name_lower = exp.Lower(this=chain_name)
    block_timestamp = coerce_to_column(block_timestamp_column)
    from_address = coerce_to_column(from_address_column)
    gas_price = coerce_to_column(gas_price_column)
    receipt_gas_used = coerce_to_column(receipt_gas_used_column)
    #time_partition = coerce_to_column(time_partition_column)

    sender_transfer_rates = (
        exp.select(
            chain_name_lower.as_("chain_name"),
            exp.DateTrunc(this=block_timestamp, unit=exp.Literal.string("hour")).as_("hr"), 
            from_address.as_("sender"),
            exp.Min(this=block_timestamp).as_("min_block_time"),
            exp.Max(this=block_timestamp).as_("max_block_time"),
            exp.Count(this="*").as_("hr_txs"),
            *additional_column_defs,
        )
        .from_(transactions_table)
        .where(exp.GT(this=gas_price, expression=exp.Literal.number(0)))
        .where(exp.GT(this=receipt_gas_used, expression=exp.Literal.number(0)))
        .group_by(exp.to_column("chain_name"), exp.to_column("hr"), exp.to_column("sender"))
    )

    first_pass_throughput_filter = (
        exp.select(
            exp.to_column("chain_name"),
            exp.to_column("sender"),
            exp.DateTrunc(this=exp.to_column("hr"), unit=exp.Literal.string("week")).as_("wk"),
            exp.Sum(this=exp.to_column("hr_txs")).as_("wk_txs"),
            exp.Max(this=exp.to_column("hr_txs")).as_("max_hr_txs"),
            exp.cast(exp.Count(this="*"), "double").div(exp.cast(exp.Literal.number(7.0 * 24.0), "double")).as_("pct_weekly_hours_active"),
            exp.Min(this=exp.to_column("min_block_time")).as_("min_block_time"),
            exp.Max(this=exp.to_column("max_block_time")).as_("max_block_time"),
        )
        #.from_(sender_transfer_rates)
        .with_("sender_transfer_rates", as_=sender_transfer_rates)
        .from_(exp.to_table("sender_transfer_rates").as_("sender_transfer_rates"))
        .group_by(exp.to_column("chain_name"), exp.to_column("sender"), exp.to_column("wk"))
        .having(
            exp.or_(
                exp.GTE(this=exp.Max(this=exp.to_column("hr_txs")), expression=exp.Literal.number(20)),
                exp.GTE(
                    this=exp.cast(exp.Count(this="*"), "double").div(exp.cast(exp.Literal.number(7.0 * 24.0), "double")),
                    expression=exp.Literal.number(0.5)
                )
            )
        )
    )
    aggregated_data = (
        exp.select(
            exp.to_column("chain_name"),
            exp.to_column("sender").as_("address"),
            exp.Max(this=exp.to_column("wk_txs")).as_("max_wk_txs"),
            exp.Max(this=exp.to_column("max_hr_txs")).as_("max_hr_txs"), 
            exp.Avg(this=exp.to_column("wk_txs")).as_("avg_wk_txs"),
            exp.Min(this=exp.to_column("min_block_time")).as_("min_block_time"),
            exp.Max(this=exp.to_column("max_block_time")).as_("max_block_time"),
            exp.Max(this=exp.to_column("pct_weekly_hours_active")).as_("max_pct_weekly_hours_active"),
            exp.Avg(this=exp.to_column("pct_weekly_hours_active")).as_("avg_pct_weekly_hours_active"),
            exp.Sum(this=exp.to_column("wk_txs")).as_("num_txs")
        )
        #.from_(first_pass_throughput_filter)
        .with_("first_pass_throughput_filter", as_=first_pass_throughput_filter)
        .from_(exp.to_table("first_pass_throughput_filter").as_("first_pass_throughput_filter"))
        .group_by(exp.to_column("chain_name"), exp.to_column("address"))
    )

    txs_per_hour = exp.cast(
        exp.TimestampDiff(
            this=exp.to_column("max_block_time"),
            expression=exp.to_column("min_block_time"),
            unit=exp.Literal.string("second")
        ),
        "double"
    ).div(exp.Literal.number(60.0 * 60.0))

    return (
        exp.select("*", txs_per_hour.as_("txs_per_hour"))
        #.from_(aggregated_data)
        .with_("aggregated_data", as_=aggregated_data)
        .from_(exp.to_table("aggregated_data").as_("aggregated_data"))
        .where(
            exp.or_(
                exp.and_(
                    exp.GTE(this=exp.to_column("max_wk_txs"), expression=exp.Literal.number(2000)),
                    exp.GTE(this=exp.to_column("max_hr_txs"), expression=exp.Literal.number(100))
                ),
                exp.and_(
                    exp.GTE(this=exp.to_column("max_wk_txs"), expression=exp.Literal.number(4000)),
                    exp.GTE(this=exp.to_column("max_hr_txs"), expression=exp.Literal.number(50))
                ),
                exp.GTE(this=exp.to_column("avg_wk_txs"), expression=exp.Literal.number(1000)),
                exp.and_(
                    exp.GTE(this=txs_per_hour, expression=exp.Literal.number(25)),
                    exp.GTE(this=exp.to_column("num_txs"), expression=exp.Literal.number(100))
                ),
                exp.GT(this=exp.to_column("avg_pct_weekly_hours_active"), expression=exp.Literal.number(0.5)),
                exp.GT(this=exp.to_column("max_pct_weekly_hours_active"), expression=exp.Literal.number(0.95))
            )
        )
    )
