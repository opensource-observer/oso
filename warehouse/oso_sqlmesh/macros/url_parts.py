from sqlglot import expressions as exp
from sqlmesh import macro
from sqlmesh.core.macros import MacroEvaluator


@macro()
def url_parts(
    evaluator: MacroEvaluator,
    url: exp.ExpOrStr,
    index: int
) -> exp.Expression:
    """
    This will parse a URI/URL, split on '/' and return the part
    - 1 is usually the domain
    - 2 is usually the first part of the path
    return the index-th part.
    """
    
    without_protocol = exp.SplitPart(
        this=url,
        delimiter=exp.Literal.string("://"),
        part_index=exp.Literal.number(2)
    )

    part = exp.SplitPart(
        this=without_protocol,
        delimiter=exp.Literal.string("/"),
        part_index=exp.Literal.number(index)
    )

    return part
