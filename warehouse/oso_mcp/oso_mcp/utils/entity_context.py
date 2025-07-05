import json
import re
from typing import Literal

import sqlglot as sg
from oso_agent.util.config import AgentConfig
from oso_agent.workflows.entity_context.llm_structured_output_workflow import (
    create_llm_structured_output_workflow,
)
from pydantic import BaseModel, Field
from sqlglot import expressions as exp


class EntityVariantsOutput(BaseModel):
    variants: list[str] = Field(..., description="Possible variants for the entity name.")

class EntitySelectionOutput(BaseModel):
    selected: str = Field(..., description="Selected canonical entity name.")

EntityType = Literal["project", "collection", "chain", "metric", "artifact"]

class EntityGuess(BaseModel):
    name: str = Field(..., description="Exact text of the entity mention")
    description: str = Field(..., description="Why this entity exists in the query")
    ranking: list[EntityType] = Field(..., description="All six entity types, ordered from most- to least-likely")

class EntityDeconstructorOutput(BaseModel):
    entities: list[EntityGuess] = Field(..., description="Extracted entities with ranked type guesses")

class ResolvedEntity(BaseModel):
    name: str = Field(..., description="Entity name")
    description: str = Field(..., description="Description of what the entity is")
    entity_type: EntityType = Field(..., description="The resolved entity type")

class EntityResolutionResult(BaseModel):
    nl_query: str = Field(..., description="Original natural language query")
    entities: list[ResolvedEntity] = Field(..., description="Successfully resolved entities")

LOOKUP_TABLE: dict[EntityType, dict[str, list[str]]] = {
    "project": {"table": ["projects_v1"], "columns": ["project_name", "display_name"]},
    "collection": {"table": ["collections_v1"], "columns": ["collection_name", "display_name"]},
    "chain": {"table": ["int_chainlist"], "columns": ["chain_name"]},
    "metric": {"table": ["metrics_v0"], "columns": ["metric_name"]},
    "artifact": {"table": ["artifacts_v1"], "columns": ["artifact_name"]}
}

async def extract_entities_from_nl_query(nl_query: str, config: AgentConfig) -> EntityDeconstructorOutput:  
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

async def generate_entity_variants(config: AgentConfig, entity: str, nl_query: str, entity_description: str) -> list[str]:
    """
    Use LLMStructuredOutputWorkflow to get possible variants for an entity name.
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

def normalize_entity_variants(variants: list[str]) -> list[str]:
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

def build_exact_entity_search_sql(entity: str, entity_type: EntityType) -> str:
    """
    Build a SQL query to search for an entity in a table by multiple columns, case/space-insensitive (exact match).
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

def build_fuzzy_entity_search_sql(variants: list[str], entity_type: EntityType) -> str:
    """
    Build a SQL query for fuzzy entity search using wildcard LIKE operations.
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

async def select_final_entity(nl_query: str, entity: str, entity_type: str, candidates: list[dict], config: AgentConfig) -> str:
    """
    Use LLMStructuredOutputWorkflow to select the best entity names from a list of candidates.
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

async def format_for_text2sql(nl_query: str, entities: list[ResolvedEntity]) -> str:
    """
    Build a formatted string that includes the nl query and resolved entities
    for consumption by the text2sql agent.
    """
    # start with the nl query
    result = f"NL Query: {nl_query}\n"
    
    # add entities section
    if entities:
        result += "Entities:\n"
        for entity in entities:
            result += f"    {entity.name} - {entity.entity_type} - {entity.description}\n"
    
    return result.strip()  # remove trailing newline