from sqlmesh import macro
from sqlmesh.core.macros import MacroEvaluator


@macro()
def regexp_like(evaluator: MacroEvaluator, column, pattern):
    if evaluator.dialect == "duckdb":
        return f"regexp_matches({column}, {pattern})"
    elif evaluator.dialect == "trino":
        return f"regexp_like({column}, {pattern})"
    else:
        return f"REGEXP_LIKE({column}, {pattern})"
