from sqlglot import expressions as exp
from sqlmesh import macro
from sqlmesh.core.macros import MacroEvaluator


def _generate_oso_id(evaluator: MacroEvaluator, *args: exp.Expression):
    """Creates a deterministic ID by concatenating the arguments and hashing them.

    Returns base64-encoded SHA256 hash for both DuckDB and Trino,
    ensuring consistency between local development and production.
    """
    if evaluator.runtime_stage == "loading":
        return exp.Literal(this="someid", is_string=True)
    concatenated = exp.Concat(expressions=args, safe=True, coalesce=False)
    if evaluator.engine_adapter.dialect == "trino":
        # Trino's SHA256 function only accepts type `varbinary`. So we convert
        # the varchar to varbinary with trino's to_utf8.
        concatenated = exp.Anonymous(this="to_utf8", expressions=[concatenated])
    sha = exp.SHA2(
        this=concatenated,
        length=exp.Literal(this=256, is_string=False),
    )

    # Convert to base64 for consistency across engines
    if evaluator.engine_adapter.dialect == "duckdb":
        # DuckDB: SHA256 returns hex VARCHAR, need to convert hex -> blob -> base64
        # Use FROM_HEX to convert hex string to BLOB, then TO_BASE64
        hex_to_blob = exp.Anonymous(this="FROM_HEX", expressions=[sha])
        return exp.ToBase64(this=hex_to_blob)
    else:
        # Trino: SHA256 already returns varbinary, can directly convert to base64
        return exp.ToBase64(this=sha)


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
