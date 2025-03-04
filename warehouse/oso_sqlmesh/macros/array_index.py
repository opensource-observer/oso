from sqlglot import expressions as exp
from sqlmesh import macro
from sqlmesh.core.macros import MacroEvaluator


@macro()
def array_index(evaluator: MacroEvaluator, index: int):
    if evaluator.runtime_stage in ["loading"]:
        return exp.Literal(this="0", is_string=False)
    # For the life of me I can't figure out how sqlmesh automatically adds 1 to
    # this index when used in a query but it does.
    return index
