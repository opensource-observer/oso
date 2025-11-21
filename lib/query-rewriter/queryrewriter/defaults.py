# Hardcoded set of ignore filters for OSO
from queryrewriter.resolvers.fqn import InferFQN
from queryrewriter.resolvers.js import JSResolver, JSResolverCallable
from queryrewriter.resolvers.legacy import LegacyTableResolver
from queryrewriter.rewrite import rewrite_query
from queryrewriter.types import TableResolver


async def default_oso_table_rewrite(
    query: str,
    org_name: str,
    final_resolver: TableResolver,
    *,
    default_dataset_name: str | None = None,
):
    """Calls the table rewriter with default settings"""

    resolvers = [
        LegacyTableResolver(),
        InferFQN(
            org_name=org_name,
            default_dataset_name=default_dataset_name,
        ),
        final_resolver,
    ]

    return await rewrite_query(query, resolvers)


async def default_oso_table_rewrite_js(
    query: str,
    org_name: str,
    js_name_resolver: JSResolverCallable,
    *,
    default_dataset_name: str | None = None,
):
    """Calls the table rewriter with default settings and a JS table resolver"""
    js_final_resolver = JSResolver(js_name_resolver)

    return await default_oso_table_rewrite(
        query,
        org_name,
        js_final_resolver,
        default_dataset_name=default_dataset_name,
    )
