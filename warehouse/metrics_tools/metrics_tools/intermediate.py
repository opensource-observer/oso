import typing as t

import duckdb
from metrics_tools.models.tools import create_basic_python_env
from sqlglot import exp
from sqlmesh import EngineAdapter
from sqlmesh.core.dialect import MacroFunc, MacroVar, parse, parse_one
from sqlmesh.core.macros import MacroEvaluator, MacroRegistry, RuntimeStage, macro


def fake_engine_adapter(dialect: str) -> EngineAdapter:
    """Return a fake engine adapter for testing purposes."""
    from sqlmesh.core.engine_adapter.duckdb import DuckDBEngineAdapter

    engine_adapter = DuckDBEngineAdapter(lambda: duckdb.connect())
    engine_adapter.dialect = dialect
    return engine_adapter


def run_macro_evaluator(
    query: str | t.List[exp.Expression] | exp.Expression,
    additional_macros: t.Optional[MacroRegistry] = None,
    variables: t.Optional[t.Dict[str, t.Any]] = None,
    runtime_stage: RuntimeStage = RuntimeStage.LOADING,
    engine_adapter: t.Optional[EngineAdapter] = None,
    default_catalog: t.Optional[str] = None,
    dialect: str = "duckdb",
):
    if isinstance(query, str):
        parsed = parse(query)
    elif isinstance(query, exp.Expression):
        parsed = [query]
    else:
        parsed = query

    macros = t.cast(MacroRegistry, macro.get_registry().copy())
    if additional_macros:
        macros.update(additional_macros)

    env = create_basic_python_env({}, "", "", macros=macros, variables=variables)

    evaluator = MacroEvaluator(
        python_env=env,
        runtime_stage=runtime_stage,
        default_catalog=default_catalog,
    )

    if engine_adapter:
        evaluator.locals["engine_adapter"] = engine_adapter
    else:
        evaluator.locals["engine_adapter"] = fake_engine_adapter(dialect)

    result: t.List[exp.Expression] = []
    for part in parsed:
        transformed = evaluator.transform(part)
        if not transformed:
            continue
        if isinstance(transformed, list):
            result.extend(transformed)
        else:
            result.append(transformed)
    return result


def run_intermediate_macro_evaluator(
    query: str | exp.Expression,
    macros: t.Optional[MacroRegistry] = None,
    variables: t.Optional[t.Dict[str, t.Any]] = None,
):
    macros = macros or t.cast(MacroRegistry, {})
    variables = variables or {}

    env = create_basic_python_env(
        {},
        "",
        "",
        macros=macros,
        variables=variables,
    )
    evaluator = MacroEvaluator(python_env=env)

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
        restored = int_expression.transform(restore_intermediate)
        if "debug" in variables:
            print("debugging intermediate macro evaluation")
            print(restored.sql(dialect=variables.get("debug_dialect", "duckdb")))
        final.append(restored)
    return final
