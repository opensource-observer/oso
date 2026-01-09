# Hardcoded set of ignore filters for OSO
from queryrewriter.resolvers.js import JSResolver, JSResolverCallable
from queryrewriter.rewrite import rewrite_query


async def default_oso_table_rewrite_js(
    query: str,
    metadata: dict,
    js_name_resolver: JSResolverCallable,
    *,
    dialect: str = "trino",
):
    """Calls the table rewriter with default settings and a JS table resolver"""
    js_resolver = JSResolver(js_name_resolver)

    return await rewrite_query(
        query, [js_resolver], metadata=metadata, input_dialect=dialect
    )
