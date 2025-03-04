from functools import reduce

from sqlglot import expressions as exp
from sqlmesh import macro
from sqlmesh.core.macros import MacroEvaluator, union
from sqlmesh.utils.errors import SQLMeshError


@macro()
def oso_union(
    evaluator: MacroEvaluator,
    kind: exp.Literal,
    type_: exp.Literal,
    *sources: exp.Expression,
) -> exp.Query:
    """
    Returns a UNION of the given CTEs or tables, selecting all columns.
    SQLMesh does not support UNIONs of CTEs, so this macro is a workaround to allow that.

    Args:
        evaluator: MacroEvaluator instance
        kind: Either 'CTE' or 'TABLE' to specify the source type.
        type_: Either 'ALL' or 'DISTINCT' for the UNION type.
        *sources: CTEs or tables to union.
    """

    union_type = type_.name.upper()
    if union_type not in ("ALL", "DISTINCT"):
        raise SQLMeshError(
            f"Invalid UNION type '{type_}'. Expected 'ALL' or 'DISTINCT'."
        )

    source_kind = kind.name.upper()
    if source_kind not in ("CTE", "TABLE"):
        raise SQLMeshError(f"Invalid kind '{kind}'. Expected 'CTE' or 'TABLE'.")

    if source_kind == "CTE":
        selects = [exp.select("*").from_(source.this) for source in sources]

        return reduce(
            lambda a, b: a.union(b, distinct=union_type == "DISTINCT"),
            selects,
        )

    return union(evaluator, type_, *sources)
