from sqlglot import expressions as exp
from sqlmesh import macro
from sqlmesh.core.macros import MacroEvaluator


def _generate_oso_id(evaluator: MacroEvaluator, *args: exp.Expression):
    """Creates a deterministic ID by concatenating the arguments and hashing them."""
    if evaluator.runtime_stage == "loading":
        return exp.Literal(this="someid", is_string=True)
    if evaluator.engine_adapter.dialect == "trino":
        # Trino's CONCAT returns NULL if any arg is NULL, unlike DuckDB which
        # treats NULLs as empty strings. Cast to VARCHAR first (handles non-string
        # types like bigint), then COALESCE with empty string for NULL safety.
        safe_args = tuple(
            exp.Coalesce(
                this=exp.Cast(this=arg, to=exp.DataType.build("VARCHAR")),
                expressions=[exp.Literal(this="", is_string=True)],
            )
            for arg in args
        )
        concatenated = exp.Concat(expressions=safe_args, safe=False, coalesce=False)
        # Trino's SHA256 function only accepts type `varbinary`. So we convert
        # the varchar to varbinary with trino's to_utf8.
        concatenated = exp.Anonymous(this="to_utf8", expressions=[concatenated])
        sha = exp.SHA2(
            this=concatenated,
            length=exp.Literal(this=256, is_string=False),
        )
        # Trino SHA256 returns varbinary, use lower(to_hex(...)) for consistent
        # lowercase hex output matching DuckDB behavior
        return exp.Lower(this=exp.Anonymous(this="to_hex", expressions=[sha]))
    # DuckDB: CONCAT is NULL-safe and SHA2 returns a hex string directly
    concatenated = exp.Concat(expressions=args, safe=True, coalesce=False)
    return exp.SHA2(
        this=concatenated,
        length=exp.Literal(this=256, is_string=False),
    )


@macro()
def oso_id(evaluator: MacroEvaluator, *args: exp.Expression):
    """Degenerate macro for backward compatibility."""
    return _generate_oso_id(evaluator, *args)


@macro()
def oso_entity_id(
    evaluator: MacroEvaluator,
    entity_source: exp.Expression,
    entity_namespace: exp.Expression,
    entity_name: exp.Expression,
) -> exp.Expression:
    """Creates a deterministic ID from entity source, namespace, and name.

    Args:
        entity_source: The source system of the entity, eg, "GITHUB"
        entity_namespace: The namespace of the entity, eg, "my-org"
        entity_name: The name of the entity, eg, "my-repo"
    """
    return _generate_oso_id(
        evaluator,
        entity_source,
        entity_namespace,
        entity_name,
    )
