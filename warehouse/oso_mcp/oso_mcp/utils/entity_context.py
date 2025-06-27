from oso_agent.util.config import AgentConfig
from oso_agent.workflows.entity_context.llm_structured_output_workflow import (
    create_llm_structured_output_workflow,
)
from pydantic import BaseModel, Field


class EntityVariantsOutput(BaseModel):
    variants: list[str] = Field(..., description="Possible variants for the entity name.")

class EntitySelectionOutput(BaseModel):
    selected: list[str] = Field(..., description="Selected canonical entity names.")

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
    prompt = (
        f"""
        You are an expert in entity context retrieval. Given the entity type: '{entity_type}',
        the user query: '{nl_query}', the original entity string: '{entity}',
        and the following candidate rows from the database (as JSON):
        {candidates}
        Return a list of the names (as strings) you are most confident are the correct mapping(s) for the user's intent.
        Return the result as a JSON object with a single key 'selected' containing a list of strings.
        """
    )
    workflow = create_llm_structured_output_workflow(config, EntitySelectionOutput)
    result = await workflow.run(input=prompt)
    return result.raw.selected

def build_fuzzy_entity_search_sql(entity_variants: list[str], table: str, columns: list[str]) -> str:
    """
    Build a SQL query using Levenshtein distance to find close matches for any of the entity variants in the relevant columns.
    Returns all possible matches with their metadata.
    """
    # For each variant, build a Levenshtein distance clause for each column
    clauses = []
    for variant in entity_variants:
        for col in columns:
            # This assumes the DB supports the levenshtein function
            clauses.append(f"levenshtein(LOWER(TRIM(CAST({col} AS VARCHAR))), LOWER('{variant}')) <= 3")
    where_clause = " OR ".join(clauses)
    sql = f"SELECT * FROM {table} WHERE {where_clause} LIMIT 20"
    return sql

def generate_entity_string_variants(variants: list[str]) -> list[str]:
    """
    Given a list of entity name variants, generate a set of deterministic variants
    with different spacings and common symbols (e.g., -, _, space, no space), all lowercased.
    Returns a list of unique variants suitable for fuzzy search.
    """
    import re
    symbols = [' ', '-', '_', '']
    result = set()
    for variant in variants:
        base = variant.strip().lower()
        # Remove all non-alphanumeric except spaces, dashes, and underscores
        alphanum = re.sub(r'[^a-z0-9\s\-_]', '', base)
        # Split on any of space, dash, or underscore
        parts = re.split(r'[\s\-_]+', alphanum)
        # Generate all joinings with allowed symbols
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