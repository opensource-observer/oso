from sqlglot import expressions as exp
from sqlmesh import macro
from sqlmesh.core.macros import MacroEvaluator


@macro()
def hex_to_int(
    evaluator: MacroEvaluator,
    hex_exp: exp.Expression,
    to_data_type: str = "BIGINT",
    to_data_type_dialect: str = "trino",
    no_prefix: bool = True,
):
    """Converts a hex string to an integer."""
    from sqlmesh.core.dialect import parse_one

    if evaluator.runtime_stage in ["loading", "creating"]:
        return parse_one("1::BIGINT", dialect="trino")

    to_data_type_exp = parse_one(
        to_data_type, dialect=to_data_type_dialect, into=exp.DataType
    )

    if evaluator.engine_adapter.dialect == "duckdb":
        if no_prefix:
            return exp.Cast(
                this=exp.Concat(
                    expressions=[exp.Literal.string("0x"), hex_exp],
                    safe=False,
                    coalesce=False,
                ),
                to=to_data_type_exp,
            )
        return exp.Cast(
            this=hex_exp,
            to=to_data_type_exp,
        )
    if evaluator.engine_adapter.dialect == "trino":
        if no_prefix:
            return exp.Cast(
                this=exp.FromBase(
                    this=hex_exp,
                    expression=exp.Literal.number(16),
                ),
                to=to_data_type_exp,
            )
        # Strip the 0x prefix from the hex string
        return exp.Cast(
            this=exp.FromBase(
                this=exp.Substring(
                    this=hex_exp,
                    start=exp.Literal.number(2),
                ),
                expression=exp.Literal.number(16),
            ),
            to=to_data_type_exp,
        )
    raise ValueError(f"Unsupported dialect: {evaluator.engine_adapter.dialect}")
