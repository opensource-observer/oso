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
    ResolvedEntity,
    build_exact_entity_search_sql,
    build_fuzzy_entity_search_sql,
    call_llm_for_entity_variants,
    call_llm_for_final_selection,
    entity_deconstructor,
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
        description="Execute a custom SQL SELECT query against the OSO data lake. Returns results as a list of records. Optionally limit the number of results for sampling.",
    )
    async def query_oso(
        sql: str,
        ctx: Context,
        limit: Optional[int] = None,
    ) -> McpResponse:
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
            #return {"success": False, "query": sql, "error": error_msg}
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
    async def query_text2sql_agent(
        natural_language_query: str,
        ctx: Context,
    ) -> McpResponse:
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
            await ctx.info(f"Converting natural language query to SQL: {natural_language_query}")
        
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
    
    @mcp.tool(
        description="Generate a SQL query from a natural language question, using entity extraction and the text2sql agent for improved accuracy.",
    )
    async def generate_sql(
        natural_language_query: str,
        ctx: Context,
    ) -> McpResponse:
        """
        Generate a SQL query from a natural language question, using entity extraction and the text2sql agent for improved accuracy.

        Args:
            natural_language_query (str): The user's question in plain English.
            ctx (Context): The request context.

        Returns:
            McpSuccessResponse: Generated SQL string.
            McpErrorResponse: On error, contains error details.

        Example:
            generate_sql("Show all projects in the Ethereum collection", ctx)
        """
        gather_all_entities_result = await gather_all_entities(natural_language_query, ctx)
        query_text2sql_agent_result = await query_text2sql_agent(gather_all_entities_result.results[0], ctx)
        return McpSuccessResponse(
            tool_name="generate_sql",
            parameters=[natural_language_query],    
            results=[query_text2sql_agent_result.results[0]],
        )
    
    @mcp.tool(
        description="Extract and resolve all relevant entities (projects, collections, metrics, etc.) from a natural language query, returning their types and context.",
    )
    async def gather_all_entities(nl_query: str, ctx: Context) -> McpResponse:
        """
        Extract and resolve all relevant entities (projects, collections, metrics, etc.) from a natural language query.

        Args:
            nl_query (str): The user's question in plain English.
            ctx (Context): The request context.

        Returns:
            McpSuccessResponse: String summary of resolved entities and their types.
            McpErrorResponse: On error, contains error details.

        Example:
            gather_all_entities("Show all projects in the Ethereum collection", ctx)
        """
        # 1. Deconstruct the query into entities using the entity_deconstructor workflow
        entity_deconstructor_result = await entity_deconstructor(nl_query, config.agent_config)
        
        # 2. For each entity, try to find it in the database using the ranking order
        resolved_entities = []
        all_models = set()      

        #print(f"Entity Deconstructor Result: {entity_deconstructor_result.entities}")
        for entity_guess in entity_deconstructor_result.entities:            
            # 3. Try each entity type in ranking order until we find a valid one
            #print(f"Entity Rankings: {entity_guess.ranking}")
            for entity_type in entity_guess.ranking:
                ##print(f"Searching for {entity_type} {entity_guess.name}")
                search_result = None

                if entity_type == "project":
                    search_result = await search_project(entity_guess.name, ctx, match_type="fuzzy", nl_query=nl_query)
                    print(f"Search result for project: {search_result}")
                elif entity_type == "collection":
                    search_result = await search_collection(entity_guess.name, ctx, match_type="fuzzy", nl_query=nl_query)
                    print(f"Search result for collection: {search_result}")
                elif entity_type == "chain":
                    search_result = await search_chain(entity_guess.name, ctx, match_type="fuzzy", nl_query=nl_query)
                    print(f"Search result for chain: {search_result}")
                elif entity_type == "metric":
                    search_result = await search_metric(entity_guess.name, ctx, match_type="fuzzy", nl_query=nl_query)
                    print(f"Search result for metric: {search_result}")
                elif entity_type == "model":
                    search_result = await search_model(entity_guess.name, ctx, match_type="fuzzy", nl_query=nl_query)
                    print(f"Search result for model: {search_result}")
                elif entity_type == "artifact":
                    search_result = await search_artifact(entity_guess.name, ctx, match_type="fuzzy", nl_query=nl_query)
                    print(f"Search result for artifact: {search_result}")
                    
                if search_result and search_result.success:
                    entity_found = ResolvedEntity(
                        row=search_result.results[0],
                        description=entity_guess.description,
                        entity_type=entity_type,
                        suggested_models=entity_guess.suggested_models
                    )
                    resolved_entities.append(entity_found)
                    all_models.update(entity_guess.suggested_models)
                    break

        # 4. Format the result as a string
        if resolved_entities:
            entity_string = ""
            for entity in resolved_entities:
                entity_string += f"""
                    Entity Rows: {entity.row}
                    Description: {entity.description}
                    Entity Type: {entity.entity_type}
                """

            final_response = f"""
                NL Query: {nl_query}
                Entities:
                    {entity_string}
                Models: {', '.join(sorted(list(all_models)))}
            """    
        else:
            final_response = f"""
                NL Query: {nl_query}
            """

        return McpSuccessResponse(
            tool_name="gather_all_entities",
            parameters=[nl_query],
            results=[final_response],
        )
    
    # I will refactor because this is a mess
    async def search_entity(
        entity: str,
        ctx: Context,
        table: str,
        columns: list[str],
        entity_type: str,
        agent_config: AgentConfig,
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
            llm_variants = await call_llm_for_entity_variants(agent_config, entity, nl_query, entity_type)
            entity_variants = generate_entity_string_variants(llm_variants)
            sql = build_fuzzy_entity_search_sql(entity_variants, table, columns)
            resp = await query_oso(sql, ctx, limit=20)
            if not (isinstance(resp, McpSuccessResponse) and resp.results):
                return McpErrorResponse(tool_name=f"search_{entity_type}", parameters=[entity], error=f"No close matches found for {entity_type} '{entity}'.")
            candidates = resp.results
            final_names = await call_llm_for_final_selection(agent_config, nl_query, entity, entity_type, candidates)
            final_results = [row for row in candidates if any(row.get(col) in final_names for col in columns)]
            return McpSuccessResponse(tool_name=f"search_{entity_type}", parameters=[entity], results=final_results)

    @mcp.tool(
        description="Search for a project by name or display name in projects_v1. Supports exact and fuzzy matching. Returns the matching row(s) if found.",
    )
    async def search_project(entity: str, ctx: Context, match_type: Literal['exact', 'fuzzy'] = 'exact', nl_query: str = "", **kwargs) -> McpResponse:
        """
        Search for a project by name or display name in projects_v1.

        Args:
            entity (str): Project name or display name.
            ctx (Context): The request context.
            match_type (Literal['exact', 'fuzzy']): Use 'exact' for strict match, 'fuzzy' for approximate match.
            nl_query (str): (Optional) The original NLQ for context.

        Returns:
            McpSuccessResponse: Matching project row(s).
            McpErrorResponse: On error, contains error details.

        Example:
            search_project("Uniswap", ctx, match_type="fuzzy")
        """
        return await search_entity(
            entity=entity,
            ctx=ctx,
            table="projects_v1",
            columns=["project_name", "display_name"],
            entity_type="project",
            match_type=match_type,
            nl_query=nl_query,
            agent_config=config.agent_config,
            **kwargs
        )

    @mcp.tool(
        description="Search for a collection by name or display name in collections_v1. Supports exact and fuzzy matching. Returns the matching row(s) if found.",
    )
    async def search_collection(entity: str, ctx: Context, match_type: Literal['exact', 'fuzzy'] = 'exact', nl_query: str = "", **kwargs) -> McpResponse:
        """
        Search for a collection by name or display name in collections_v1.

        Args:
            entity (str): Collection name or display name.
            ctx (Context): The request context.
            match_type (Literal['exact', 'fuzzy']): Use 'exact' for strict match, 'fuzzy' for approximate match.
            nl_query (str): (Optional) The original NLQ for context.

        Returns:
            McpSuccessResponse: Matching collection row(s).
            McpErrorResponse: On error, contains error details.

        Example:
            search_collection("ethereum-github", ctx, match_type="exact")
        """
        return await search_entity(
            entity=entity,
            ctx=ctx,
            table="collections_v1",
            columns=["collection_name", "display_name"],
            entity_type="collection",
            match_type=match_type,
            nl_query=nl_query,
            agent_config=config.agent_config,
            **kwargs
        )

    @mcp.tool(
        description="Search for a chain/network by name in int_chainlist. Supports exact and fuzzy matching. Returns the matching row(s) if found.",
    )
    async def search_chain(entity: str, ctx: Context, match_type: Literal['exact', 'fuzzy'] = 'exact', nl_query: str = "", **kwargs) -> McpResponse:
        """
        Search for a chain/network by name in int_chainlist.

        Args:
            entity (str): Chain/network name.
            ctx (Context): The request context.
            match_type (Literal['exact', 'fuzzy']): Use 'exact' for strict match, 'fuzzy' for approximate match.
            nl_query (str): (Optional) The original NLQ for context.

        Returns:
            McpSuccessResponse: Matching chain row(s).
            McpErrorResponse: On error, contains error details.

        Example:
            search_chain("Optimism", ctx, match_type="fuzzy")
        """
        return await search_entity(
            entity=entity,
            ctx=ctx,
            table="int_chainlist",
            columns=["chainlist_name", "oso_chain_name", "display_name"],
            entity_type="chain",
            match_type=match_type,
            nl_query=nl_query,
            agent_config=config.agent_config,
            **kwargs
        )

    @mcp.tool(
        description="Search for a metric by display name in metrics_v0. Supports exact and fuzzy matching. Returns the matching row(s) if found.",
    )
    async def search_metric(entity: str, ctx: Context, match_type: Literal['exact', 'fuzzy'] = 'exact', nl_query: str = "", **kwargs) -> McpResponse:
        """
        Search for a metric by display name in metrics_v0.

        Args:
            entity (str): Metric display name.
            ctx (Context): The request context.
            match_type (Literal['exact', 'fuzzy']): Use 'exact' for strict match, 'fuzzy' for approximate match.
            nl_query (str): (Optional) The original NLQ for context.

        Returns:
            McpSuccessResponse: Matching metric row(s).
            McpErrorResponse: On error, contains error details.

        Example:
            search_metric("GITHUB_commits_daily", ctx, match_type="exact")
        """
        return await search_entity(
            entity=entity,
            ctx=ctx,
            table="metrics_v0",
            columns=["display_name"],
            entity_type="metric",
            match_type=match_type,
            nl_query=nl_query,
            agent_config=config.agent_config,
            **kwargs
        )

    @mcp.tool(
        description="Search for a model by name in models_v1. Supports exact and fuzzy matching. Returns the matching row(s) if found.",
    )
    async def search_model(entity: str, ctx: Context, match_type: Literal['exact', 'fuzzy'] = 'exact', nl_query: str = "", **kwargs) -> McpResponse:
        """
        Search for a model by name in models_v1.

        Args:
            entity (str): Model name.
            ctx (Context): The request context.
            match_type (Literal['exact', 'fuzzy']): Use 'exact' for strict match, 'fuzzy' for approximate match.
            nl_query (str): (Optional) The original NLQ for context.

        Returns:
            McpSuccessResponse: Matching model row(s).
            McpErrorResponse: On error, contains error details.

        Example:
            search_model("project_funding_summary", ctx, match_type="exact")
        """
        return await search_entity(
            entity=entity,
            ctx=ctx,
            table="models_v1",
            columns=["model_name"],
            entity_type="model",
            match_type=match_type,
            nl_query=nl_query,
            agent_config=config.agent_config,
            **kwargs
        )

    @mcp.tool(
        description="Search for an artifact by name in artifacts_v1. Supports exact and fuzzy matching. Returns the matching row(s) if found.",
    )
    async def search_artifact(entity: str, ctx: Context, match_type: Literal['exact', 'fuzzy'] = 'exact', nl_query: str = "", **kwargs) -> McpResponse:
        """
        Search for an artifact by name in artifacts_v1.

        Args:
            entity (str): Artifact name.
            ctx (Context): The request context.
            match_type (Literal['exact', 'fuzzy']): Use 'exact' for strict match, 'fuzzy' for approximate match.
            nl_query (str): (Optional) The original NLQ for context.

        Returns:
            McpSuccessResponse: Matching artifact row(s).
            McpErrorResponse: On error, contains error details.

        Example:
            search_artifact("@libp2p/echo", ctx, match_type="fuzzy")
        """
        return await search_entity(
            entity=entity,
            ctx=ctx,
            table="artifacts_v1",
            columns=["artifact_name"],
            entity_type="artifact",
            match_type=match_type,
            nl_query=nl_query,
            agent_config=config.agent_config,
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
            
            Welcome to the OSO Data Lake Explorer! This server provides a suite of tools for querying and exploring the OSO (Open Source Observer) data lake.
            
            ## Workflows & Tools
            
            ### 1. Data Exploration
            - **list_tables**: List all available tables in the data lake.
            - **get_table_schema**: Get the schema (columns, types) for a specific table.
            - **get_sample_queries**: See example SQL queries for common tasks.
            - **query_oso**: Run custom SQL SELECT queries and get results as records.
            
            ### 2. Natural Language to SQL
            - **generate_sql**: Go from a natural language question to a SQL query, with entity extraction for accuracy.
            
            ## Best Practices
            - Use **generate_sql** for most NLQ-to-SQL tasks (it handles entity context).
            - Use **list_tables** and **get_table_schema** to explore available data.
            - Use **get_sample_queries** for inspiration and copy-paste examples.
            
            ## Troubleshooting
            - If you get an error about a missing table or column, use **list_tables** and **get_table_schema** to check names.
            - Ensure your OSO API key is set as the `OSO_API_KEY` environment variable.
            
            ## Authentication
            This server requires an OSO API key to be set as the `OSO_API_KEY` environment variable.
        """)

    return mcp
