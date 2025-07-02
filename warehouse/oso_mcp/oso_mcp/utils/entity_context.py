import json
from typing import Literal

from oso_agent.util.config import AgentConfig
from oso_agent.workflows.entity_context.llm_structured_output_workflow import (
    create_llm_structured_output_workflow,
)
from pydantic import BaseModel, Field


class EntityVariantsOutput(BaseModel):
    variants: list[str] = Field(..., description="Possible variants for the entity name.")

class EntitySelectionOutput(BaseModel):
    selected: list[str] = Field(..., description="Selected canonical entity names.")

EntityType = Literal["project", "collection", "chain", "metric", "model", "artifact"]

class EntityGuess(BaseModel):
    name: str = Field(..., description="Exact text of the entity mention")
    description: str = Field(..., description="Why this entity exists in the query")
    ranking: list[EntityType] = Field(..., description="All six entity types, ordered from most- to least-likely")
    suggested_models: list[str] = Field(default=[], description="Optional list of specific model names mentioned in the prompt that are relevant for this entity")

class EntityDeconstructorOutput(BaseModel):
    entities: list[EntityGuess] = Field(..., description="Extracted entities with ranked type guesses")

class ResolvedEntity(BaseModel):
    row: dict = Field(..., description="Entity row")
    description: str = Field(..., description="Description of what the entity is")
    entity_type: EntityType = Field(..., description="The resolved entity type")
    suggested_models: list[str] = Field(default=[], description="Models suggested for this entity")

class EntityResolutionResult(BaseModel):
    nl_query: str = Field(..., description="Original natural language query")
    entities: list[ResolvedEntity] = Field(..., description="Successfully resolved entities")
    models: list[str] = Field(..., description="All unique models from resolved entities")

async def call_llm_for_entity_variants(config: AgentConfig, entity: str, nl_query: str, entity_type: str) -> list[str]:
    """
    Use LLMStructuredOutputWorkflow to get possible variants for an entity name.
    """
    # Build the prompt for the LLM
    prompt = (
        f"""
        You are an expert in entity context retrieval. Given the following entity type: '{entity_type}',
        the user query: '{nl_query}', and the entity string: '{entity}',
        return a list of all possible spellings, versions, and ways this entity could appear in a database.
        Do NOT worry about case or whitespace or Levenshtein distance; focus on real-world naming variations, synonyms, or alternate forms (e.g., 'arbitrum' -> 'arbitrum-one').
        Return the result as a JSON object with a single key 'variants' containing a list of strings.
        """
    )
    workflow = create_llm_structured_output_workflow(config, EntityVariantsOutput)
    result = await workflow.run(input=prompt)
    return result.raw.variants

async def call_llm_for_final_selection(config: AgentConfig, nl_query: str, entity: str, entity_type: str, candidates: list[dict]) -> list[str]:
    """
    Use LLMStructuredOutputWorkflow to select the best entity names from a list of candidates.
    """
    # Build the prompt for the LLM
    prompt = f"""
        You are an expert at mapping user-supplied entity strings to the correct
        OSO Data Lake rows.

        ────────────────────────────────────────────────────────────────────────
        INPUTS
        ────────────────────────────────────────────────────────────────────────
        • **Entity type**: {entity_type}
        • **Original phrase**: “{entity}”
        • **User query**: “{nl_query}”
        • **Candidate rows** (JSON array):  
        {json.dumps(candidates, indent=2)}
        ────────────────────────────────────────────────────────────────────────
        TASK
        ────────────────────────────────────────────────────────────────────────

        Infer the user's intent from the query.

        Decide which candidate rows best satisfy that intent.

        Return 1 to 3 names (strings) only if you are confident they map
        to the intended entity.
        • If one row is clearly correct, return just that one.
        • If several rows are plausibly interchangeable (e.g., aliases or
        different namespaces for the same thing), return up to three, in
        descending order of confidence.

        If none of the rows looks appropriate, return an empty list.

        ────────────────────────────────────────────────────────────────────────
        OUTPUT — MUST BE VALID JSON WITH THIS SHAPE
        ────────────────────────────────────────────────────────────────────────
        {{
            "selected": ["name 1", "name 2", "name 3"]
        }}
        Return no other keys.
    """
    workflow = create_llm_structured_output_workflow(config, EntitySelectionOutput)
    result = await workflow.run(input=prompt)
    return result.raw.selected

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

def build_fuzzy_entity_search_sql(
    variants: list[str],
    table: str,
    columns: list[str],
    *,
    limit: int = 50,
    levenshtein_max: int = 3,
    like_budget: int | None = None,
) -> str:
    """
    Build a fuzzy-match SQL query that
      1) prioritises wildcard (%variant%) matches
      2) falls back to Levenshtein <= levenshtein_max
         **and** requires at least that many shared letters.
    """
    # how many rows to try to fetch via LIKE first
    like_budget = like_budget or max(1, limit // 2)

    like_clauses, lev_clauses = [], []
    for v in variants:
        clean = v.strip().lower()
        if not clean:
            continue

        # WILDCARD  (%variant%)
        if len(like_clauses) < like_budget:
            for col in columns:
                like_clauses.append(
                    f"LOWER({col}) LIKE '%{clean.replace('%', '')}%'"
                )

        # LEVENSHTEIN  (distance + shared-letters gate)
        # distance allowance scales with variant length but is capped
        dist_allow = min(levenshtein_max, len(clean))
        for col in columns:
            overlap_expr = (
                f"length(regexp_replace(LOWER({col}), '[^a-z]', '', 'g'))  "
                f"- length(regexp_replace(LOWER({col}) "
                f"|| '{clean}', '(.)\\1', '', 'g'))"
            )
            lev_clauses.append(
                "("
                f"levenshtein(LOWER({col}), '{clean}') <= {dist_allow} "
                f"AND {overlap_expr} >= {dist_allow}"
                ")"
            )

    # assemble WHERE
    where_parts = []
    if like_clauses:
        where_parts.append("(" + " OR ".join(like_clauses) + ")")
    if lev_clauses:
        # only add Levenshtein part if we *didn't* reach the limit with LIKE
        where_parts.append("(" + " OR ".join(lev_clauses) + ")")

    where_sql = " OR ".join(where_parts) if where_parts else "FALSE"

    # order: LIKE hits first (distance = 0), then shortest Levenshtein
    distance_order = ", ".join(
        [f"levenshtein(LOWER({c}), '{variants[0].lower()}')" for c in columns]
    )

    return (
        f"SELECT *\n"
        f"FROM {table}\n"
        f"WHERE {where_sql}\n"
        f"ORDER BY ({distance_order}) ASC\n"
        f"LIMIT {limit}"
    )

def generate_entity_string_variants(variants: list[str]) -> list[str]:
    """
    Given a list of entity name variants, generate a set of deterministic variants
    with different spacings and common symbols (e.g., -, _, space, no space), all lowercased.
    If SQL wildcards (%) are present, returns minimal variants since wildcards provide flexibility.
    Returns a list of unique variants suitable for fuzzy search.
    """
    import re

    # Check if any variant contains SQL wildcards
    has_wildcards = any('%' in variant for variant in variants)
    
    result = set()
    for variant in variants:
        base = variant.strip().lower()
        
        if has_wildcards:
            # If wildcards are present, just add the cleaned base variant
            # Don't generate many variants since wildcards already provide pattern matching
            if base:
                result.add(base)
        else:
            # Original behavior: generate many variants for fuzzy matching
            # Remove all non-alphanumeric except spaces, dashes, and underscores
            alphanum = re.sub(r'[^a-z0-9\s\-_]', '', base)
            # Split on any of space, dash, or underscore
            parts = re.split(r'[\s\-_]+', alphanum)
            # Generate all joinings with allowed symbols
            symbols = [' ', '-', '_', '']
            for sym in symbols:
                joined = sym.join(parts)
                if joined:
                    result.add(joined)
            # Also add the original base and alphanum
            if base:
                result.add(base)
            if alphanum:
                result.add(alphanum)
    
    return list(result)

async def entity_deconstructor(nl_query: str, config: AgentConfig) -> EntityDeconstructorOutput:  
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
        5. Provide any suggestions for what models the SQL builder should use to query
        the entity on this context. 

        ────────────────────────────────────────────────────────────────────────
        ENTITY TYPES
        ────────────────────────────────────────────────────────────────────────
        - **project**     - open-source project          (`projects_v1`)
        - **collection**  - set of projects              (`collections_v1`)
        - **chain**       - L1/L2 network                (`int_chainlist`)
        - **metric**      - KPI or time-series measure   (`metrics_*` tables)
            • *Key-metric totals*:  `key_metrics_by_%`
            • *Time-series*:        `timeseries_metrics_by_%`
            ▸ Metric names follow **SOURCE_metricname_timeagg**  
                (e.g., **GITHUB_closed_issues_weekly**).  
            ▸ Time aggs are one of: **daily, weekly, monthly, yearly**.  
            ▸ If the source is wild-carded, use a leading '%'  
                (e.g., **%active_users_daily**).

        - **model**       - analytical model             (`models_v1`)
        - **artifact**    - software artifact            (`artifacts_v1`)

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
                ],
                "suggested_models": ["optional list of models to use to query the entity"]
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
                "ranking": ["collection", "project", "chain", "metric", "model", "artifact"],
                "suggested_models": ["projects_by_collection_v1"]
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