import typing as t

from metrics_tools.models import (
    create_basic_python_env,
)

from sqlmesh.core.macros import MacroEvaluator, MacroRegistry
from sqlmesh.core.dialect import parse_one, MacroVar, MacroFunc
from sqlglot import exp


def intermediate_macro_evaluator(
    query: str | exp.Expression,
    macros: t.Optional[MacroRegistry] = None,
    variables: t.Optional[t.Dict[str, t.Any]] = None,
):
    env = create_basic_python_env(
        {},
        "",
        "",
        macros=macros,
        variables=variables,
    )
    evaluator = MacroEvaluator(python_env=env)
    macros = macros or t.cast(MacroRegistry, {})
    variables = variables or {}

    if isinstance(query, str):
        parsed = parse_one(query)
    else:
        parsed = query

    def replace_all_macro_vars(node: exp.Expression):
        if not isinstance(node, MacroVar):
            return node
        # If the variables are set in this environment then allow them to be
        # evaluated
        if node.this in variables:
            return node
        # All others are unknown
        return exp.Anonymous(
            this="$$INTERMEDIATE_MACRO_VAR",
            expressions=[exp.Literal(this=node.this, is_string=True)],
        )

    def replace_all_macro_funcs(node: exp.Expression):
        if not isinstance(node, MacroFunc):
            return node
        # if this is an anonymous function then it's a macrofunc
        if isinstance(node.this, exp.Anonymous):
            if node.this.this in macros:
                return node
            else:
                recursed_transform = node.this.transform(replace_all_macro_funcs)
                return exp.Anonymous(
                    this="$$INTERMEDIATE_MACRO_FUNC",
                    expressions=[
                        recursed_transform,
                    ],
                )
        raise Exception("expected node.this to be an anonymous expression")

    parsed = parsed.transform(replace_all_macro_vars)
    parsed = parsed.transform(replace_all_macro_funcs)

    intermediate_evaluation = evaluator.transform(parsed)
    if not intermediate_evaluation:
        return intermediate_evaluation

    def restore_intermediate(node: exp.Expression):
        if not isinstance(node, exp.Anonymous):
            return node
        if not node.this.startswith("$$INTERMEDIATE"):
            return node
        if node.this == "$$INTERMEDIATE_MACRO_VAR":
            return MacroVar(this=node.expressions[0].this)
        elif node.this == "$$INTERMEDIATE_MACRO_FUNC":
            # Restore all recursive expressions
            recursed_transform = node.expressions[0].transform(restore_intermediate)
            return MacroFunc(this=recursed_transform)
        else:
            raise Exception(f"Unknown anonymous intermediate reference `{node.this}`")

    if not isinstance(intermediate_evaluation, list):
        intermediate_evaluation = [intermediate_evaluation]
    final: t.List[exp.Expression] = []
    for int_expression in intermediate_evaluation:
        final.append(int_expression.transform(restore_intermediate))
    return final
