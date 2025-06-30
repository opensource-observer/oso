import textwrap
import uuid
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import Generic, List, Literal, Optional, TypeVar, Union

import requests
from mcp.server.fastmcp import Context, FastMCP
from oso_agent.util.config import AgentConfig
from pyoso import Client

from ..utils.entity_context import (
    build_fuzzy_entity_search_sql,
    call_llm_for_entity_variants,
    call_llm_for_final_selection,
    generate_entity_string_variants,
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

        client = Client(api_key)
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
        description="Run a SQL query against the OSO data lake",
    )
    async def query_oso(
        sql: str,
        ctx: Context,
        limit: Optional[int] = None,
    ) -> McpResponse:
        """
        Run a SQL query against the OSO data lake.

        Args:
            sql: SQL query to execute (SELECT statements only)
            limit: Optional limit to apply to the query results

        Returns:
            Dict containing query results and metadata
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
            #return {"success": False, "query": sql, "error": error_msg}
            return response


    @mcp.tool(
        description="List all available tables in the OSO data lake",
    )
    async def list_tables(ctx: Context) -> McpResponse:
        """
        List all available tables in the OSO data lake.

        Returns:
            Dict containing list of available tables
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
            #return {"success": True, "tables": tables}
        except Exception as e:
            error_msg = str(e)
            if ctx:
                await ctx.error(f"Failed to list tables: {error_msg}")

            response = McpErrorResponse(
                tool_name="list_tables",
                error=error_msg,
            )
            return response
            #return {"success": False, "error": error_msg}


    @mcp.tool(
        description="Get the schema for a specific table in the OSO data lake",
    )
    async def get_table_schema(
        table_name: str,
        ctx: Context,
    ) -> McpResponse:
        """
        Get the schema for a specific table in the OSO data lake.

        Args:
            table_name: Name of the table to get schema for

        Returns:
            Dict containing table schema information
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
            #return {"success": True, "table": table_name, "schema": schema}
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
            #return {"success": False, "table": table_name, "error": error_msg}


    @mcp.tool(
        description="Get a set of sample queries to help users get started with the OSO data lake",
    )
    async def get_sample_queries(ctx: Context) -> McpResponse:
        """
        Get a set of sample queries to help users get started with the OSO data lake.

        Returns:
            Dict containing sample queries with descriptions
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
        #return { "success": True, "samples": samples }

    @mcp.tool(
        description="Use a text2sql agent to generate a SQL query from a natural language query",
    )
    async def query_text2sql_agent(
        natural_language_query: str,
        ctx: Context,
    ) -> McpResponse:
        """
        Use a text2sql agent to generate a SQL query from a natural language query.
        
        Args:
            natural_language_query: The natural language query to convert to SQL
            
        Returns:
            Dict containing the generated SQL query
        """
        if ctx:
            await ctx.info(f"Converting natural language query to SQL: {natural_language_query}")
        
        config = ctx.request_context.lifespan_context.config
        if not config:
            raise ValueError("Config is not available in the context")
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
            "messages": [{"role": "user", "content": natural_language_query}],
        }

        response = requests.post(url, json=data, headers=headers)

        return McpSuccessResponse(
            tool_name="query_text2sql_agent",
            parameters=[natural_language_query],
            results=[response.json()["sql"]],
        )

    def build_exact_entity_search_sql(entity: str, table: str, columns: list[str]) -> str:
        """
        Build a SQL query to search for an entity in a table by multiple columns, case/space-insensitive (exact match).
        Args:
            entity: The entity string to search for
            table: The table to search in
            columns: List of columns to search
        Returns:
            SQL query string
        """
        norm_entity = entity.strip().lower().replace("'", "''")
        conditions = [
            f"LOWER(TRIM(CAST({col} AS VARCHAR))) = '{norm_entity}'" for col in columns
        ]
        where_clause = " OR ".join(conditions)
        sql = f"SELECT * FROM {table} WHERE {where_clause} LIMIT 1"
        return sql
    
    async def search_entity(
        entity: str,
        ctx: Context,
        table: str,
        columns: list[str],
        entity_type: str,
        match_type: Literal['exact', 'fuzzy'] = 'exact',
        nl_query: str = "",
        **kwargs
    ) -> McpResponse:
        """
        Generic search function for entities (project, collection, chain, etc.)
        """
        if match_type == 'exact':
            sql = build_exact_entity_search_sql(entity, table, columns)
            resp = await query_oso(sql, ctx, limit=1)
            if isinstance(resp, McpSuccessResponse) and resp.results:
                return McpSuccessResponse(tool_name=f"search_{entity_type}", parameters=[entity], results=resp.results)
            else:
                return McpErrorResponse(tool_name=f"search_{entity_type}", parameters=[entity], error=f"{entity_type.capitalize()} '{entity}' not found.")
        else:
            config = AgentConfig()
            llm_variants = await call_llm_for_entity_variants(config, entity, nl_query, entity_type)
            entity_variants = generate_entity_string_variants(llm_variants)
            sql = build_fuzzy_entity_search_sql(entity_variants, table, columns)
            resp = await query_oso(sql, ctx, limit=20)
            if not (isinstance(resp, McpSuccessResponse) and resp.results):
                return McpErrorResponse(tool_name=f"search_{entity_type}", parameters=[entity], error=f"No close matches found for {entity_type} '{entity}'.")
            candidates = resp.results
            final_names = await call_llm_for_final_selection(config, nl_query, entity, entity_type, candidates)
            final_results = [row for row in candidates if any(row.get(col) in final_names for col in columns)]
            return McpSuccessResponse(tool_name=f"search_{entity_type}", parameters=[entity], results=final_results)

    @mcp.tool(
        description="Search for a project by name or display name in projects_v1. Returns the row if found, else not found.",
    )
    async def search_project(entity: str, ctx: Context, match_type: Literal['exact', 'fuzzy'] = 'exact', nl_query: str = "", **kwargs) -> McpResponse:
        return await search_entity(
            entity=entity,
            ctx=ctx,
            table="projects_v1",
            columns=["project_name", "display_name"],
            entity_type="project",
            match_type=match_type,
            nl_query=nl_query,
            **kwargs
        )

    @mcp.tool(
        description="Search for a collection by name or display name in collections_v1. Returns the row if found, else not found.",
    )
    async def search_collection(entity: str, ctx: Context, match_type: Literal['exact', 'fuzzy'] = 'exact', nl_query: str = "", **kwargs) -> McpResponse:
        return await search_entity(
            entity=entity,
            ctx=ctx,
            table="collections_v1",
            columns=["collection_name", "display_name"],
            entity_type="collection",
            match_type=match_type,
            nl_query=nl_query,
            **kwargs
        )

    @mcp.tool(
        description="Search for a chain/network by name in int_chainlist. Returns the row if found, else not found.",
    )
    async def search_chain(entity: str, ctx: Context, match_type: Literal['exact', 'fuzzy'] = 'exact', nl_query: str = "", **kwargs) -> McpResponse:
        return await search_entity(
            entity=entity,
            ctx=ctx,
            table="int_chainlist",
            columns=["chainlist_name", "oso_chain_name", "display_name"],
            entity_type="chain",
            match_type=match_type,
            nl_query=nl_query,
            **kwargs
        )

    @mcp.tool(
        description="Search for a metric by display name in metrics_v0. Returns the row if found, else not found.",
    )
    async def search_metric(entity: str, ctx: Context, match_type: Literal['exact', 'fuzzy'] = 'exact', nl_query: str = "", **kwargs) -> McpResponse:
        return await search_entity(
            entity=entity,
            ctx=ctx,
            table="metrics_v0",
            columns=["display_name"],
            entity_type="metric",
            match_type=match_type,
            nl_query=nl_query,
            **kwargs
        )

    @mcp.tool(
        description="Search for a model by name in models_v1. Returns the row if found, else not found.",
    )
    async def search_model(entity: str, ctx: Context, match_type: Literal['exact', 'fuzzy'] = 'exact', nl_query: str = "", **kwargs) -> McpResponse:
        return await search_entity(
            entity=entity,
            ctx=ctx,
            table="models_v1",
            columns=["model_name"],
            entity_type="model",
            match_type=match_type,
            nl_query=nl_query,
            **kwargs
        )

    @mcp.tool(
        description="Search for an artifact by name in artifacts_v1. Returns the row if found, else not found.",
    )
    async def search_artifact(entity: str, ctx: Context, match_type: Literal['exact', 'fuzzy'] = 'exact', nl_query: str = "", **kwargs) -> McpResponse:
        return await search_entity(
            entity=entity,
            ctx=ctx,
            table="artifacts_v1",
            columns=["artifact_name"],
            entity_type="artifact",
            match_type=match_type,
            nl_query=nl_query,
            **kwargs
        )

    @mcp.resource("help://getting-started")
    def get_help_guide() -> str:
        """
        Resource providing help information about using the OSO data lake server.

        Returns:
            str: Help information as a string
        """

        return textwrap.dedent("""
            # OSO Data Lake Explorer - Getting Started
            
            This MCP server provides tools for querying and exploring the OSO (Open Source Observer) data lake.
            
            ## Available Tools
            
            1. `query_oso` - Run custom SQL queries against the data lake
            2. `list_tables` - Get a list of all available tables
            3. `get_table_schema` - Retrieve the schema for a specific table
            4. `get_sample_queries` - Get sample queries to help you get started
            5. `query_text2sql_agent` - Use a text2sql agent to generate a SQL query from a natural language query
            
            ## Authentication
            
            This server requires an OSO API key to be set as the `OSO_API_KEY` environment variable.
        """)

    return mcp
