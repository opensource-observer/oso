from sqlglot import expressions as exp
from sqlmesh import macro
from sqlmesh.core.macros import MacroEvaluator


@macro()
def sha1_hex(
    evaluator: MacroEvaluator,
    string_exp: exp.Expression,
):
    """
    Computes the SHA1 hash of a string and returns it as a lowercase hex string.
    
    This macro provides cross-dialect support for SHA1 hashing:
    - Trino: LOWER(TO_HEX(SHA1(CAST(string AS VARBINARY))))
    - DuckDB: SHA1(string)
    
    Args:
        evaluator: The macro evaluator
        string_exp: The string expression to hash
        
    Returns:
        An expression that computes the SHA1 hash as a lowercase hex string
    """
    from sqlmesh.core.dialect import parse_one

    if evaluator.runtime_stage == "loading":
        return parse_one("'hash'::VARCHAR", dialect="trino")

    if evaluator.engine_adapter.dialect == "duckdb":
        # DuckDB's SHA1 function directly returns a hex string
        return exp.Anonymous(
            this="sha1",
            expressions=[string_exp],
        )
    
    if evaluator.engine_adapter.dialect == "trino":
        # Trino requires: LOWER(TO_HEX(SHA1(CAST(string AS VARBINARY))))
        return exp.Lower(
            this=exp.Anonymous(
                this="to_hex",
                expressions=[
                    exp.Anonymous(
                        this="sha1",
                        expressions=[
                            exp.Cast(
                                this=string_exp,
                                to=exp.DataType.build("VARBINARY"),
                            )
                        ],
                    )
                ],
            )
        )
    
    raise ValueError(f"Unsupported dialect: {evaluator.engine_adapter.dialect}")
