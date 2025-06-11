import typing as t

from ...util.jaccard import jaccard_similarity_set
from ...util.query import (
    determine_query_type,
    determine_sql_models_used,
    sanitize_query_from_agent,
)


def sql_query_type_similarity(output: str, metadata: dict[str, t.Any]) -> float:
    """Evaluate the similarity between the output and expected SQL query types using Jaccard similarity."""
    output = sanitize_query_from_agent(output)
    output_query_types = determine_query_type(output)
    expected_query_types = metadata.get('query_type') or []

    return jaccard_similarity_set(set(output_query_types), set(expected_query_types))

def sql_oso_models_used_similarity(output: str, metadata: dict[str, t.Any]) -> float:
    """Evaluate the similarity between the output and expected oso models used using Jaccard similarity."""
    output = sanitize_query_from_agent(output)
    output_oso_models_used = determine_sql_models_used(output)
    expected_oso_models_used = metadata.get('sql_models_used') or []

    return jaccard_similarity_set(set(output_oso_models_used), set(expected_oso_models_used))
