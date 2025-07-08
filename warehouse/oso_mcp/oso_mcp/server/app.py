import textwrap
import uuid
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import Generic, List, Literal, Optional, TypeVar, Union

import requests
from mcp.server.fastmcp import Context, FastMCP
from pyoso import Client

from ..utils.entity_context import (
    EntityType,
    ResolvedEntity,
    build_exact_entity_search_sql,
    build_fuzzy_entity_search_sql,
    extract_entities_from_nl_query,
    format_for_text2sql,
    generate_entity_variants,
    normalize_entity_variants,
    select_final_entity,
)
from .config import MCPConfig

MCP_SSE_PORT = 8000

P = TypeVar("P")
R = TypeVar("R")

@dataclass
class McpErrorResponse(Generic[P]):
    tool_name: str
    error: str
    success: bool = False
    parameters: Optional[List[P]] = None

@dataclass
class McpSuccessResponse(Generic[P, R]):
    tool_name: str
    results: List[R]
    success: bool = True
    parameters: Optional[List[P]] = None

McpResponse = Union[McpErrorResponse[P], McpSuccessResponse[P, R]]

@dataclass
class AppContext:
    oso_client: Optional[Client] = None

def default_lifespan(config: MCPConfig):
    @asynccontextmanager
    async def app_lifespan(_server: FastMCP) -> AsyncIterator[AppContext]:
        """Manage application lifecycle with OSO client in context"""
        api_key = config.oso_api_key

        client = Client(api_key.get_secret_value())
        context = AppContext(oso_client=client)

        try:
            yield context
        finally:
            pass
    return app_lifespan


def setup_mcp_app(config: MCPConfig):

    mcp = FastMCP(
        "OSO Data Lake Explorer",
        port=config.port,
        host=config.host,
        dependencies=["pyoso", "python-dotenv", "requests"],
        lifespan=default_lifespan(config),
    )

    @mcp.tool(
        description="Execute a custom SQL SELECT query against the OSO data lake. Returns results as a list of records. Optionally limit the number of results for sampling.",
    )
    async def query_oso(sql: str, ctx: Context, limit: Optional[int] = None) -> McpResponse:
        """
        Execute a SQL SELECT query against the OSO data lake.

        Args:
            sql (str): The SQL SELECT query to execute. Only SELECT statements are supported.
            ctx (Context): The request context.
            limit (Optional[int]): If provided, limits the number of returned records (unless LIMIT is already present).

        Returns:
            McpSuccessResponse: On success, contains a list of result records.
            McpErrorResponse: On error, contains error details.

        Example:
            query_oso("SELECT * FROM collections_v1", ctx, limit=5)
        """
        if ctx:
            await ctx.info(f"Executing query: {sql}")

        if limit is not None:
            sql_upper = sql.upper().strip()

            if "LIMIT" not in sql_upper.split() and limit is not None:
                sql = f"{sql.rstrip(';')} LIMIT {limit}"
            elif limit is not None and ctx:
                await ctx.warning(
                    "LIMIT clause already exists in query; ignoring limit parameter"
                )

        try:
            oso_client: Optional[Client] = ctx.request_context.lifespan_context.oso_client
            if not oso_client:
                raise ValueError("OSO client is not available in the context")

            df = oso_client.to_pandas(sql)

            results = df.to_dict(orient="records")

            response = McpSuccessResponse(
                tool_name="query_oso",
                parameters=[sql],
                results=results,
            )

            return response
        except Exception as e:
            error_msg = str(e)
            if ctx:
                await ctx.error(f"Query failed: {error_msg}")

            response = McpErrorResponse(
                tool_name="query_oso",
                parameters=[sql],
                error=error_msg,
            )
            # return {"success": False, "query": sql, "error": error_msg}
            return response

    @mcp.tool(
        description="Retrieve a list of all available tables in the OSO data lake, including their names and metadata.",
    )
    async def list_tables(ctx: Context) -> McpResponse:
        """
        List all available tables in the OSO data lake.

        Args:
            ctx (Context): The request context.

        Returns:
            McpSuccessResponse: List of tables and metadata.
            McpErrorResponse: On error, contains error details.

        Example:
            list_tables(ctx)
        """
        try:
            oso_client: Optional[Client] = ctx.request_context.lifespan_context.oso_client
            if not oso_client:
                raise ValueError("OSO client is not available in the context")

            df = oso_client.to_pandas("SHOW TABLES")

            tables = df.to_dict(orient="records")

            response = McpSuccessResponse(
                tool_name="list_tables",
                results=tables,
            )
            return response
            # return {"success": True, "tables": tables}
        except Exception as e:
            error_msg = str(e)
            if ctx:
                await ctx.error(f"Failed to list tables: {error_msg}")

            response = McpErrorResponse(
                tool_name="list_tables",
                error=error_msg,
            )
            return response
            # return {"success": False, "error": error_msg}

    @mcp.tool(
        description="Get the column schema (names, types, etc.) for a specified table in the OSO data lake.",
    )
    async def get_table_schema(
        table_name: str,
        ctx: Context,
    ) -> McpResponse:
        """
        Get the schema (column names, types, etc.) for a specific table in the OSO data lake.

        Args:
            table_name (str): Name of the table (see list_tables).
            ctx (Context): The request context.

        Returns:
            McpSuccessResponse: Table schema as a list of columns.
            McpErrorResponse: On error, contains error details.

        Example:
            get_table_schema("collections_v1", ctx)
        """
        try:
            oso_client: Optional[Client] = ctx.request_context.lifespan_context.oso_client
            if not oso_client:
                raise ValueError("OSO client is not available in the context")

            schema_query = f"DESCRIBE {table_name}"
            df = oso_client.to_pandas(schema_query)
            schema = df.to_dict(orient="records")

            response = McpSuccessResponse(
                tool_name="get_table_schema",
                parameters=[table_name],
                results=schema,
            )
            return response
            # return {"success": True, "table": table_name, "schema": schema}
        except Exception as e:
            error_msg = str(e)
            if ctx:
                await ctx.error(f"Failed to get schema for {table_name}: {error_msg}")

            response = McpErrorResponse(
                tool_name="get_table_schema",
                parameters=[table_name],
                error=error_msg,
            )
            return response
            # return {"success": False, "table": table_name, "error": error_msg}

    @mcp.tool(
        description="Retrieve a curated set of example SQL queries and their descriptions to help users get started with common OSO data lake tasks.",
    )
    async def get_sample_queries(ctx: Context) -> McpResponse:
        """
        Get a set of sample SQL queries and their descriptions for common OSO data lake tasks.

        Args:
            ctx (Context): The request context.

        Returns:
            McpSuccessResponse: List of sample queries and descriptions.

        Example:
            get_sample_queries(ctx)
        """
        samples = [
            {
                "name": "All Collections",
                "description": "Get the names of all collections on OSO",
                "query": """
                SELECT
                collection_name,
                display_name
                FROM collections_v1
                ORDER BY collection_name
                """,
            },
            {
                "name": "Projects in Collection",
                "description": "Get the names of all projects in the Ethereum GitHub collection",
                "query": """
                SELECT
                project_id,
                project_name
                FROM projects_by_collection_v1
                WHERE collection_name = 'ethereum-github'
                """,
            },
            {
                "name": "Collection Code Metrics",
                "description": "Get GitHub commit metrics for the Ethereum GitHub collection",
                "query": """
                SELECT
                tm.sample_date,
                tm.amount
                FROM timeseries_metrics_by_collection_v0 AS tm
                JOIN collections_v1 AS c ON tm.collection_id = c.collection_id
                JOIN metrics_v0 AS m ON tm.metric_id = m.metric_id
                WHERE
                    c.collection_name = 'ethereum-github'
                    AND m.metric_name = 'GITHUB_commits_daily'
                ORDER BY 1
                """,
            },
            {
                "name": "Collection Onchain Metrics",
                "description": "Get onchain metrics for projects in a collection",
                "query": """
                SELECT
                tm.sample_date,
                tm.amount
                FROM timeseries_metrics_by_collection_v0 AS tm
                JOIN collections_v1 AS c ON tm.collection_id = c.collection_id
                JOIN metrics_v0 AS m ON tm.metric_id = m.metric_id
                WHERE
                    c.collection_name = 'op-retrofunding-4'
                    AND m.metric_name = 'BASE_gas_fees_weekly'
                ORDER BY 1
                """,
            },
            {
                "name": "Project Funding History",
                "description": "Get the complete funding history for Uniswap",
                "query": """
                SELECT
                time,
                event_source,
                from_project_name as funder,
                amount,
                grant_pool_name
                FROM oss_funding_v0
                WHERE to_project_name = 'uniswap'
                ORDER BY time DESC
                """,
            },
            {
                "name": "Top Funded Projects",
                "description": "Find the projects that have received the most funding",
                "query": """
                SELECT
                to_project_name,
                COUNT(DISTINCT event_source) as funding_sources,
                COUNT(*) as number_of_grants,
                SUM(amount) as total_funding
                FROM oss_funding_v0
                GROUP BY to_project_name
                HAVING total_funding > 0
                ORDER BY total_funding DESC
                LIMIT 20
                """,
            },
            {
                "name": "Repository Dependencies",
                "description": "Get package dependencies for Ethereum Go implementation",
                "query": """
                SELECT *
                FROM sboms_v0
                WHERE from_artifact_id = '0mjl8VhWsui_6TEZZnbQzyf8h1A9bOioIlK17p0D5hI='
                """,
            },
            {
                "name": "Package Maintainers",
                "description": "Find the repository that maintains a specific package",
                "query": """
                SELECT
                package_artifact_source,
                package_artifact_name,
                package_owner_project_id,
                package_owner_artifact_namespace,
                package_owner_artifact_name
                FROM package_owners_v0
                WHERE package_artifact_name = '@libp2p/echo'
                """,
            },
        ]
        response = McpSuccessResponse(
            tool_name="get_sample_queries",
            results=samples,
        )
        return response

    @mcp.tool(
        description="Convert a natural language question into a SQL query using the OSO text2sql agent. Returns the generated SQL string.",
    )
    async def query_text2sql_agent(nl_query: str, ctx: Context) -> McpResponse:
        """
        Convert a natural language question into a SQL query using the OSO text2sql agent.

        Args:
            natural_language_query (str): The user's question in plain English.
            ctx (Context): The request context.

        Returns:
            McpSuccessResponse: Generated SQL string.
            McpErrorResponse: On error, contains error details.

        Example:
            query_text2sql_agent("Show all projects in the Ethereum collection", ctx)
        """
        if ctx:
            await ctx.info(f"Converting natural language query to SQL: {nl_query}")
        
        api_key = config.oso_api_key
        if not api_key:
            raise ValueError("OSO API key is not available in the context")

        url = "https://www.opensource.observer/api/v1/text2sql"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

        data = {
            "id": str(uuid.uuid4()),
            "messages": [{"role": "user", "content": nl_query}],
        }

        response = requests.post(url, json=data, headers=headers)

        return McpSuccessResponse(
            tool_name="query_text2sql_agent",
            parameters=[nl_query],
            results=[response.json()["sql"]],
        )

    @mcp.tool(
        description="Generate a SQL query from a natural language question, using entity extraction and the text2sql agent for improved accuracy.",
    )
    async def generate_sql(nl_query: str, ctx: Context) -> McpResponse:
        # extract and search for all entities in the query
        gather_all_entities_result = await gather_all_entities_and_search(nl_query, ctx)
        # format the entities and the nl query into a string for the text2sql agent
        entities_plus_nl_query = await format_for_text2sql(nl_query, gather_all_entities_result)
        # call the text2sql agent to generate the sql query
        query_text2sql_agent_result = await query_text2sql_agent(entities_plus_nl_query, ctx)
        return query_text2sql_agent_result
    
    # nl query in -> list of resolved entities out
    async def gather_all_entities_and_search(nl_query: str, ctx: Context) -> list[ResolvedEntity]:
        # extract entities from the query 
        entity_deconstructor_result = await extract_entities_from_nl_query(nl_query, config)
    
        resolved_entities = []
        # handle each entity one at a time
        for entity_guess in entity_deconstructor_result.entities:            
            # generate the variants
            llm_generated_variants = await generate_entity_variants(config, entity_guess.name, nl_query, entity_guess.description)
            # normalize the variants
            normalized_variants = normalize_entity_variants(llm_generated_variants)
            # then iterate over the ranking of entity types
            for entity_type in entity_guess.ranking:
                # build the sql query
                sql = build_fuzzy_entity_search_sql(normalized_variants, entity_type)
                # execute the query
                resp = await query_oso(sql, ctx)
                
                if isinstance(resp, McpSuccessResponse) and resp.results:
                    # select the correct row from the search result
                    selected_row = await select_final_entity(nl_query, entity_guess.name, entity_type, resp.results, config)
                    # if we have a selected row, we can add it to the list of resolved entities
                    if selected_row:
                        entity_found = ResolvedEntity(
                            name=selected_row,
                            description=entity_guess.description,
                            entity_type=entity_type,
                        )
                        resolved_entities.append(entity_found)
                    break
            # if we aren't successful at finding an entity for now we will assume the entity doesn't exist and ignore it
        return resolved_entities
    
    @mcp.tool(
        description="Search for an entity by name or display name in a specific table. Supports exact and fuzzy matching. Returns the matching row(s) if found.",
    )
    async def search_entity(entity: str, entity_type: EntityType, ctx: Context, nl_query: str, match_type: Literal['exact', 'fuzzy'] = 'exact', **kwargs) -> McpResponse:
        """
        Generic search function for entities (project, collection, chain, etc.)
        """

        if match_type == 'fuzzy':
            # generate the variants
            llm_generated_variants = await generate_entity_variants(config, entity, nl_query, entity_type)
            # normalize the variants
            normalized_variants = normalize_entity_variants(llm_generated_variants)
            # build the sql query
            sql = build_fuzzy_entity_search_sql(normalized_variants, entity_type)
        else:
            # build the sql query
            sql = build_exact_entity_search_sql(entity, entity_type)

        # execute the query
        resp = await query_oso(sql, ctx, limit=1)
        return resp

    @mcp.resource("help://getting-started")
    def get_help_guide() -> str:
        """
        Resource providing help information about using the OSO data lake server.

        Returns:
            str: Help information as a string
        """

        return textwrap.dedent("""
            # OSO Data Lake Explorer - Getting Started
            
            Welcome to the OSO Data Lake Explorer! This server provides a suite of tools for querying and exploring the OSO (Open Source Observer) data lake.
            
            ## Available Tools
            
            ### 1. Data Exploration
            - **list_tables**: List all available tables in the data lake
            - **get_table_schema**: Get the schema (columns, types) for a specific table
            - **get_sample_queries**: See curated example SQL queries for common tasks
            - **query_oso**: Execute custom SQL SELECT queries and get results as records
            
            ### 2. Natural Language to SQL
            - **generate_sql**: Convert natural language questions to SQL using entity extraction + text2sql agent (RECOMMENDED)
            - **query_text2sql_agent**: Direct conversion of natural language to SQL using the text2sql agent
            
            ### 3. Entity Search
            - **search_entity**: Search for specific entities (projects, collections, chains) by name with exact or fuzzy matching
            
            ## Recommended Workflows
            
            ### Getting Started
            1. Use **list_tables** to see available data
            2. Use **get_table_schema** to understand table structures
            3. Use **get_sample_queries** for inspiration and patterns
            
            ### Natural Language Queries
            1. Use **generate_sql** for most natural language questions (handles entity resolution automatically)
            2. Use **query_text2sql_agent** for simpler queries that don't require entity context
            
            ### Direct SQL Queries
            1. Use **query_oso** to execute custom SQL queries directly
            2. Add `limit` parameter for sampling large result sets
            
            ## Best Practices
            - **generate_sql** is the most powerful tool for natural language queries as it includes entity extraction
            - Use **search_entity** when you need to verify entity names before building queries
            - Start with **get_sample_queries** to understand common query patterns
            - Use **list_tables** and **get_table_schema** to explore the data structure
            
            ## Troubleshooting
            - If you get errors about missing tables/columns, use **list_tables** and **get_table_schema**
            - If entity names aren't found, try **search_entity** with fuzzy matching
            - Ensure your OSO API key is set as the `OSO_API_KEY` environment variable
            
            ## Authentication
            This server requires an OSO API key to be set as the `OSO_API_KEY` environment variable.
        """)

    return mcp
