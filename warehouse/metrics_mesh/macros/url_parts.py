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
    if evaluator.runtime_stage in ["loading"]:
        return exp.Literal(this="0", is_string=False)
    
    protocol_split = exp.Split(
        this=url,
        expression=exp.Literal(this="://")
    )

    without_protocol = exp.NthValue(
        this=protocol_split,
        offset=exp.Literal.number(2),
    )

    parts_split = exp.Split(
        this=without_protocol,
        expression=exp.Literal(this="/")
    )

    part = exp.NthValue(
        this=parts_split,
        offset=exp.Literal.number(index),
    )

    return part
