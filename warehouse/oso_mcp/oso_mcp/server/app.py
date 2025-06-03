import textwrap
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import Generic, List, Optional, TypeVar, Union

from mcp.server.fastmcp import Context, FastMCP
from pyoso import Client

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
            
            ## Authentication
            
            This server requires an OSO API key to be set as the `OSO_API_KEY` environment variable.
        """)

    return mcp
