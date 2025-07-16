"""
TEMPORARY DUMP FILE - NOT FOR PRODUCTION USE

This file contains entity context and SQL generation functionality that was moved
out of the MCP server. It's currently a dump of various functions and will 
eventually be refactored and integrated into the oso_agent workflow properly.

This is just a temporary location to store all these functions while we 
reorganize the codebase structure.
"""

import json
import re
import textwrap
from typing import Any, Dict, List, Literal, Optional

import sqlglot as sg
from oso_agent.util.config import AgentConfig
from oso_agent.workflows.entity_context.llm_structured_output_workflow import (
    create_llm_structured_output_workflow,
)
from pydantic import BaseModel, Field
from pyoso import Client
from sqlglot import exp


# Pydantic Models
class EntityVariantsOutput(BaseModel):
    variants: list[str] = Field(description="Possible variants for the entity name.")


class EntitySelectionOutput(BaseModel):
    selected: str = Field(description="Selected canonical entity name.")


EntityType = Literal["project", "collection", "chain", "metric", "artifact"]


class EntityGuess(BaseModel):
    name: str = Field(description="Exact text of the entity mention")
    description: str = Field(description="Why this entity exists in the query")
    ranking: list[EntityType] = Field(description="All six entity types, ordered from most- to least-likely")


class EntityDeconstructorOutput(BaseModel):
    entities: list[EntityGuess] = Field(description="Extracted entities with ranked type guesses")


class ResolvedEntity(BaseModel):
    name: str = Field(description="Entity name")
    description: str = Field(description="Description of what the entity is")
    entity_type: EntityType = Field(description="The resolved entity type")


class EntityResolutionResult(BaseModel):
    nl_query: str = Field(description="Original natural language query")
    entities: list[ResolvedEntity] = Field(description="Successfully resolved entities")


# Constants
LOOKUP_TABLE: dict[EntityType, dict[str, list[str]]] = {
    "project": {"table": ["projects_v1"], "columns": ["project_name", "display_name"]},
    "collection": {"table": ["collections_v1"], "columns": ["collection_name", "display_name"]},
    "chain": {"table": ["int_chainlist"], "columns": ["chain_name"]},
    "metric": {"table": ["metrics_v0"], "columns": ["metric_name"]},
    "artifact": {"table": ["artifacts_v1"], "columns": ["artifact_name"]}
}


# Helper Functions for SQL Generation and Entity Resolution
# prev MCP tool (can be a tool in the agent workflow)
async def query_oso(sql: str, oso_client: Client, limit: Optional[int] = None) -> Dict[str, Any]:
    """
    Execute a SQL SELECT query against the OSO data lake.

    Args:
        sql (str): The SQL SELECT query to execute. Only SELECT statements are supported.
        oso_client (Client): The OSO client instance.
        limit (Optional[int]): If provided, limits the number of returned records (unless LIMIT is already present).

    Returns:
        Dict[str, Any]: Success response with results or error response with error details.

    Example:
        query_oso("SELECT * FROM collections_v1", client, limit=5)
    """
    if limit is not None:
        sql_upper = sql.upper().strip()

        if "LIMIT" not in sql_upper.split() and limit is not None:
            sql = f"{sql.rstrip(';')} LIMIT {limit}"

    try:
        df = oso_client.to_pandas(sql)
        results = df.to_dict(orient="records")
        
        return {
            "success": True,
            "query": sql,
            "results": results,
        }
    except Exception as e:
        error_msg = str(e)
        return {
            "success": False,
            "query": sql,
            "error": error_msg,
        }

# prev MCP tool (can be a tool in the agent workflow)
async def list_tables(oso_client: Client) -> Dict[str, Any]:
    """
    List all available tables in the OSO data lake.

    Args:
        oso_client (Client): The OSO client instance.

    Returns:
        Dict[str, Any]: List of tables and metadata or error details.

    Example:
        list_tables(client)
    """
    try:
        df = oso_client.to_pandas("SHOW TABLES")
        tables = df.to_dict(orient="records")
        
        return {
            "success": True,
            "tables": tables,
        }
    except Exception as e:
        error_msg = str(e)
        return {
            "success": False,
            "error": error_msg,
        }

# prev MCP tool (can be a tool in the agent workflow)
async def get_table_schema(table_name: str, oso_client: Client) -> Dict[str, Any]:
    """
    Get the schema (column names, types, etc.) for a specific table in the OSO data lake.

    Args:
        table_name (str): Name of the table (see list_tables).
        oso_client (Client): The OSO client instance.

    Returns:
        Dict[str, Any]: Table schema as a list of columns or error details.

    Example:
        get_table_schema("collections_v1", client)
    """
    try:
        schema_query = f"DESCRIBE {table_name}"
        df = oso_client.to_pandas(schema_query)
        schema = df.to_dict(orient="records")
        
        return {
            "success": True,
            "table": table_name,
            "schema": schema,
        }
    except Exception as e:
        error_msg = str(e)
        return {
            "success": False,
            "table": table_name,
            "error": error_msg,
        }

# prev MCP tool (can be a tool in the agent workflow)
def get_sample_queries() -> Dict[str, Any]:
    """
    Get a set of sample SQL queries and their descriptions for common OSO data lake tasks.

    Returns:
        Dict[str, Any]: List of sample queries and descriptions.

    Example:
        get_sample_queries()
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
    
    return {
        "success": True,
        "samples": samples,
    }

# helper function with previous MCP server (likely out of scope)
async def generate_sql(nl_query: str, oso_client: Client, config: AgentConfig) -> str:
    """
    Generate a SQL query from a natural language question, using entity extraction and the text2sql agent for improved accuracy.
    
    Args:
        nl_query (str): Natural language query
        oso_client (Client): OSO client instance
        config (AgentConfig): Agent configuration
        
    Returns:
        str: Generated SQL query
    """
    # extract and search for all entities in the query
    gather_all_entities_result = await gather_all_entities_and_search(nl_query, oso_client, config)
    # format the entities and the nl query into a string for the text2sql agent
    entities_plus_nl_query = await format_for_text2sql(nl_query, gather_all_entities_result)
    # call the text2sql agent to generate the sql query
    # Note: query_text2sql_agent function needs to be imported/implemented separately
    # query_text2sql_agent_result = await query_text2sql_agent(entities_plus_nl_query, config)
    # For now, return the formatted string
    return entities_plus_nl_query

# helper function to run the entire entity search workflow (this can be incorporated into the agent workflow)
async def gather_all_entities_and_search(nl_query: str, oso_client: Client, config: AgentConfig) -> List[ResolvedEntity]:
    """
    Extract and resolve all entities from a natural language query.
    
    Args:
        nl_query (str): Natural language query
        oso_client (Client): OSO client instance
        config (AgentConfig): Agent configuration
        
    Returns:
        List[ResolvedEntity]: List of resolved entities
    """
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
            resp = await query_oso(sql, oso_client)
            
            if resp.get("success") and resp.get("results"):
                # select the correct row from the search result
                selected_row = await select_final_entity(nl_query, entity_guess.name, entity_type, resp["results"], config)
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

# helper function with previous MCP server (likely out of scope)
async def search_entity(
    entity: str, 
    entity_type: EntityType, 
    oso_client: Client, 
    nl_query: str, 
    config: AgentConfig,
    match_type: Literal['exact', 'fuzzy'] = 'exact', 
    **kwargs
) -> Dict[str, Any]:
    """
    Generic search function for entities (project, collection, chain, etc.)
    
    Args:
        entity (str): Entity name to search for
        entity_type (EntityType): Type of entity
        oso_client (Client): OSO client instance
        nl_query (str): Original natural language query for context
        config (AgentConfig): Agent configuration
        match_type (Literal['exact', 'fuzzy']): Search match type
        
    Returns:
        Dict[str, Any]: Search results
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
    resp = await query_oso(sql, oso_client, limit=1)
    return resp

# prev MCP tool (can be a tool in the agent workflow)
def get_help_guide() -> str:
    """
    Get help information about using the OSO data lake.

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

# helper function for the agent workflow to extract entities from a natural language query
# this step is included in the latest agent workflow version (just needs to be refactored)
async def extract_entities_from_nl_query(nl_query: str, config: AgentConfig) -> EntityDeconstructorOutput:  
    """
    Extract entities from a natural language query using LLM structured output.
    
    Args:
        nl_query (str): Natural language query
        config (AgentConfig): Agent configuration
        
    Returns:
        EntityDeconstructorOutput: Extracted entities with type rankings
    """
    # call an LLM with the nl_query and extract entities with clues of what type to default to 
    prompt = """
        You are an **Entity Deconstructor** for the OSO Data Lake.
        Your output feeds an automated SQL-builder, so precision matters.

        ────────────────────────────────────────────────────────────────────────
        TASK
        ────────────────────────────────────────────────────────────────────────
        1. Read the user's natural-language question.  
        2. Extract every phrase that **might** name a concrete OSO entity  
        (never generic words like "project" or "collection").  
        3. For each entity, return **all six entity types ranked** from most- to
        least-likely, choosing #1 strictly by what can be joined with the
        SQL models and cross-entity tables listed below.
        4. Include a brief description about what you think the entity is.

        ────────────────────────────────────────────────────────────────────────
        ENTITY TYPES
        ────────────────────────────────────────────────────────────────────────
        - **project**     - open-source project        
        - **collection**  - set of projects             
        - **chain**       - L1/L2 network               
        - **metric**      - KPI or time-series measure  
            • *Key-metric totals*:  `key_metrics_by_%`
            • *Time-series*:        `timeseries_metrics_by_%`
            ▸ Metric names follow **SOURCE_metricname_timeagg**  
                (e.g., **GITHUB_closed_issues_weekly**).  
            ▸ Time aggs are typically one of: **daily, weekly, monthly, yearly**.  
            ▸ If the source is wild-carded, use a leading '%'  
                (e.g., **%active_users_daily**).

        - **artifact**    - github repo, contracts, dependencies, etc.

        ────────────────────────────────────────────────────────────────────────
        CROSS-ENTITY TABLES (for tiebreak reasoning; do **NOT** output)
        ────────────────────────────────────────────────────────────────────────
        projects_by_collection_v1
        artifacts_by_collection_v1
        artifacts_by_project_v1
        artifacts_by_user_v1
        timeseries_metrics_by_collection_v0
        timeseries_metrics_by_project_v0
        timeseries_metrics_by_artifact_v0
        key_metrics_by_collection_v0
        key_metrics_by_project_v0
        key_metrics_by_artifact_v0

        ────────────────────────────────────────────────────────────────────────
        OUTPUT — MUST MATCH EntityDeconstructorOutput
        ────────────────────────────────────────────────────────────────────────
        ```json
        {
            "entities": [
                {
                "name": "original phrase",
                "description": "one short sentence explaining what it probably is",
                "ranking": [
                    "most-likely type",
                    "2nd",
                    "3rd",
                    "4th",
                    "5th",
                    "least-likely type"
                ]
                },
                …
            ]
        }
        Return all six types in every ranking, in lower-case exactly as shown above.
        Do not include any other text in your output.

        ────────────────────────────────────────────────────────────────────────
        EXAMPLE WITH LOGIC AND OUTPUT
        ────────────────────────────────────────────────────────────────────────
        User Query: "How many projects under Optimism?"

        Logic:
        1. "Optimism" is the entity to extract
        2. The question asks about "projects under Optimism", suggesting a parent-child relationship
        3. Looking at cross-entity tables: projects_by_collection_v1 exists (projects can belong to collections)
        4. No direct table exists for projects under a chain
        5. Therefore "Optimism" is most likely a collection, not a chain
        6. We know we need projects data at the collection level so we recommended projects_by_collection_v1

        ```json
        {
            "entities": [
                {
                "name": "Optimism",
                "description": "Most likely a collection of projects in the Optimism ecosystem",
                "ranking": ["collection", "project", "chain", "metric", "model", "artifact"]
                }
            ]
        }

        ────────────────────────────────────────────────────────────────────────
        USER QUESTION
        ────────────────────────────────────────────────────────────────────────
    """ + f"{nl_query}"

    workflow = create_llm_structured_output_workflow(config, EntityDeconstructorOutput)
    result = await workflow.run(input=prompt)

    return result.raw

# helper function for the agent workflow to extract entities from a natural language query
# this step is included in the latest agent workflow version (just needs to be refactored)
async def generate_entity_variants(config: AgentConfig, entity: str, nl_query: str, entity_description: str) -> list[str]:
    """
    Use LLMStructuredOutputWorkflow to get possible variants for an entity name.
    
    Args:
        config (AgentConfig): Agent configuration
        entity (str): Entity name
        nl_query (str): Original natural language query
        entity_description (str): Description of the entity
        
    Returns:
        list[str]: List of entity variants
    """
    # build the prompt for the llm
    prompt = (
        f"""
        You are an expert in generating variants for crypto-related entities. 
        You will be given a target entity, a description of what the entity is, and a NL query for context on why the entity matters.
        Your job is to generate a list of different spellings, versions, and ways the same entity could be represented in a database.
        Don't worry about case or whitespace as everything will be normalized, focus more on real-world naming variations, synonyms, or alternate forms.

        Here is the user query: '{nl_query}'
        Here is the entity: '{entity}'
        Here is the entity description: '{entity_description}'

        Examples:

            1. Entity: "Optimism"
            Description: "Optimism is a Layer 2 scaling solution for Ethereum"
            NL Query: "How many projects are on Optimism?"
            Variants: ["optimism", "op", "optimism-ethereum", "op-coin", "optimism-coin", "optimism-protocol"]

            2. Entity: "Arbitrum"
            Description: "Arbitrum is a Layer 2 scaling solution for Ethereum"
            NL Query: "How many projects are on Arbitrum?"
            Variants: ["arbitrum", "arb", "arbitrum-one", "arbitrum-nova"]

            3. Entity: "Retro Funding Round 7"
            Description: "Retro Funding Round 7 was a funding round for a project"
            NL Query: "How many projects were involved with Retro Funding Round 7?"
            Variants: ["retro-funding", "op-retrofunding-7", "op-retrofunding-s7", "retrofunding-s7", "retro-funding-s7"]

        Return the result as a JSON object with a single key 'variants' containing a list of strings.
        """
    )
    workflow = create_llm_structured_output_workflow(config, EntityVariantsOutput)
    result = await workflow.run(input=prompt)
    return result.raw.variants

# helper function for the agent workflow to extract entities from a natural language query
# this step is included in the latest agent workflow version (just needs to be refactored)
def normalize_entity_variants(variants: list[str]) -> list[str]:
    """
    Normalize entity variants by cleaning and generating different joining patterns.
    
    Args:
        variants (list[str]): List of entity variants
        
    Returns:
        list[str]: Normalized variants
    """
    result = set()
    
    for variant in variants:
        # normalize: lowercase and strip whitespace
        base = variant.strip().lower()
        if not base:
            continue
            
        # remove all non-alphanumeric except spaces, dashes, and underscores
        alphanum = re.sub(r'[^a-z0-9\s\-_]', '', base)
        
        # split on any whitespace, dash, or underscore to get word parts
        parts = re.split(r'[\s\-_]+', alphanum)
        parts = [part for part in parts if part]  # remove empty parts
        
        if not parts:
            continue
            
        # generate all possible joinings with different symbols
        symbols = [' ', '-', '_', '']  # space, dash, underscore, no separator
        
        for symbol in symbols:
            joined = symbol.join(parts)
            if joined:
                result.add(joined)
        
        # also add the original normalized base
        if base:
            result.add(base)
        if alphanum and alphanum != base:
            result.add(alphanum)
    
    # return sorted list for deterministic output
    return sorted(list(result))

# helper function for the agent workflow to extract entities from a natural language query
# this step is included in the latest agent workflow version (just needs to be refactored)
def build_exact_entity_search_sql(entity: str, entity_type: EntityType) -> str:
    """
    Build a SQL query to search for an entity in a table by multiple columns, case/space-insensitive (exact match).
    
    Args:
        entity (str): Entity name to search for
        entity_type (EntityType): Type of entity
        
    Returns:
        str: SQL query string
    """    
    table = LOOKUP_TABLE[entity_type]["table"][0]
    columns = LOOKUP_TABLE[entity_type]["columns"]
    
    norm_entity = entity.strip().lower()
    
    # build conditions using sqlglot expressions
    conditions = []
    for col in columns:
        # build: LOWER(TRIM(CAST(col AS VARCHAR))) = ?
        col_expr = sg.func("LOWER", sg.func("TRIM", sg.func("CAST", sg.column(col), exp.DataType.build("VARCHAR"))))
        condition = sg.condition(col_expr).eq(exp.Literal.string(norm_entity))
        conditions.append(condition)
    
    # combine conditions with OR
    where_condition = conditions[0]
    for cond in conditions[1:]:
        where_condition = where_condition.or_(cond)
    
    # build the full query
    query = sg.select("*").from_(table).where(where_condition).limit(1)
    
    return query.sql()

# probably out of scope, not sure if we will be doing fuzzy/exact matching since we are generating variants + normalizing them
def build_fuzzy_entity_search_sql(variants: list[str], entity_type: EntityType) -> str:
    """
    Build a SQL query for fuzzy entity search using wildcard LIKE operations.
    
    Args:
        variants (list[str]): List of entity variants
        entity_type (EntityType): Type of entity
        
    Returns:
        str: SQL query string
    """
    if entity_type not in LOOKUP_TABLE:
        raise ValueError(f"Invalid entity type: {entity_type}")
    
    table = LOOKUP_TABLE[entity_type]["table"][0]
    columns = LOOKUP_TABLE[entity_type]["columns"]
    
    # build conditions for each variant against each column
    conditions = []
    for variant in variants:
        clean_variant = variant.strip().lower()
        if not clean_variant:
            continue
            
        # create wildcard pattern: %variant%
        wildcard_pattern = f"%{clean_variant}%"
        
        for col in columns:
            # build: LOWER(col) LIKE '%variant%'
            col_expr = sg.func("LOWER", sg.column(col))
            condition = col_expr.like(exp.Literal.string(wildcard_pattern))
            conditions.append(condition)
    
    if not conditions:
        # if no valid variants, return a query that returns no results
        query = sg.select("*").from_(table).where(sg.condition("FALSE"))
    else:
        # combine all conditions with OR
        where_condition = conditions[0]
        for cond in conditions[1:]:
            where_condition = where_condition.or_(cond)
        
        # build the full query
        query = sg.select("*").from_(table).where(where_condition)
    
    return query.sql()

# helper function for the agent workflow to extract entities from a natural language query
# this step is included in the latest agent workflow version (just needs to be refactored)
async def select_final_entity(nl_query: str, entity: str, entity_type: str, candidates: list[dict], config: AgentConfig) -> str:
    """
    Use LLMStructuredOutputWorkflow to select the best entity names from a list of candidates.
    
    Args:
        nl_query (str): Original natural language query
        entity (str): Entity name from query
        entity_type (str): Type of entity
        candidates (list[dict]): List of candidate entities
        config (AgentConfig): Agent configuration
        
    Returns:
        str: Selected entity name or empty string if not confident
    """
    # build the prompt for the llm
    prompt = f"""
        You are an expert at mapping user-supplied entity strings to the correct
        OSO Data Lake rows.

        ────────────────────────────────────────────────────────────────────────
        INPUTS
        ────────────────────────────────────────────────────────────────────────
        • **Entity type**: {entity_type}
        • **Original phrase**: "{entity}"
        • **User query**: "{nl_query}"
        • **Candidate rows** (JSON array):  
        {json.dumps(candidates, indent=2)}
        ────────────────────────────────────────────────────────────────────────
        TASK
        ────────────────────────────────────────────────────────────────────────

        Infer the user's intent from the query.

        Decide which candidate rows best satisfy that intent.

        Return the name of the entity that is most likely to be the intended entity.

        If you are not confident in your selection, return the empty string.

        ────────────────────────────────────────────────────────────────────────
        OUTPUT — MUST BE VALID JSON WITH THIS SHAPE
        ────────────────────────────────────────────────────────────────────────
        {{
            "selected": str
        }}
        Return no other keys.
    """
    workflow = create_llm_structured_output_workflow(config, EntitySelectionOutput)
    result = await workflow.run(input=prompt)
    return result.raw.selected

# helper function with previous MCP server (likely out of scope)
async def format_for_text2sql(nl_query: str, entities: list[ResolvedEntity]) -> str:
    """
    Build a formatted string that includes the nl query and resolved entities
    for consumption by the text2sql agent.
    
    Args:
        nl_query (str): Original natural language query
        entities (list[ResolvedEntity]): List of resolved entities
        
    Returns:
        str: Formatted string for text2sql agent
    """
    # start with the nl query
    result = f"NL Query: {nl_query}\n"
    
    # add entities section
    if entities:
        result += "Entities:\n"
        for entity in entities:
            result += f"    {entity.name} - {entity.entity_type} - {entity.description}\n"
    
    return result.strip()  # remove trailing newline