from sqlglot import exp
from sqlmesh import macro
from sqlmesh.core.macros import MacroEvaluator


@macro()
def oso_source(evaluator: MacroEvaluator, table_name: exp.Expression):
    """Uses the global variables `oso_source_db` and `oso_source_catalog` to
    return a table"""
    table_name_evaled = evaluator.eval_expression(table_name)
    table_name_str = ""

    if isinstance(table_name_evaled, (exp.Literal, exp.Identifier)):
        table_name_str = table_name_evaled.this
    elif isinstance(table_name_evaled, exp.Table):
        table_name_str = table_name_evaled.this.this
    else:
        raise ValueError(f"Unexpected table name: {table_name_evaled}")

    oso_source_catalog = evaluator.var("oso_source_catalog")
    oso_source_db = evaluator.var("oso_source_db")

    if not oso_source_db:
        raise ValueError("Required variable `oso_source_schema` is not set")

    return exp.Table(
        this=exp.to_identifier(table_name_str),
        db=exp.to_identifier(oso_source_db),
        catalog=exp.to_identifier(oso_source_catalog),
    )
