"""
This module defines a LlamaIndex tool for translating natural language
queries into structured semantic queries using a specialized LLM.
"""

import logging
from functools import partial
from typing import Optional

from llama_index.core import PromptTemplate
from llama_index.core.base.response.schema import Response
from llama_index.core.llms import LLM
from llama_index.core.tools import FunctionTool
from oso_semantic.definition import SemanticQuery as StructuredSemanticQuery

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """
TASK: Convert a natural language query into a valid SemanticQuery JSON object for the OSO data warehouse.

# ERROR FEEDBACK (IF RETRYING)
{error_feedback}

# REQUIRED JSON FORMAT
```json
{
    "name": "optional_query_name",
    "description": "optional_description", 
    "selects": ["model.attribute", "model.measure"],
    "filters": ["model.attribute = 'value'"],
    "limit": 100
}
```

# CORE CONCEPTS
- **Models**: artifacts, projects, collections, repositories, contracts
- **Attributes**: Non-aggregated data (artifact_name, project_name, language)
- **Measures**: Aggregated data (count, distinct_count, total_stars, avg_stars) 
- **Relationships**: Use `->` to traverse (artifacts.by_project->projects.project_name)

# VALID RELATIONSHIPS
- `artifacts.by_project->projects.*`
- `artifacts.by_collection->collections.*` 
- `projects.by_collection->collections.*`
- Multi-hop: `artifacts.by_project->projects.by_collection->collections.*`

# KEY EXAMPLES

**Count Query**: "How many GitHub artifacts?"
```json
{
    "selects": ["artifacts.count"],
    "filters": ["artifacts.artifact_source = 'GITHUB'"]
}
```

**Cross-Model**: "Show project names and their collections"
```json
{
    "selects": [
        "projects.project_name", 
        "projects.by_collection->collections.collection_name"
    ]
}
```

**Repository Analysis**: "TypeScript repos with >1000 stars"
```json
{
    "selects": ["repositories.artifact_name", "repositories.language", "repositories.star_count"],
    "filters": ["repositories.language = 'TypeScript'", "repositories.star_count > 1000"]
}
```

# CRITICAL RULES
- ❌ NEVER use raw SQL: `COUNT(*)`, `SUM()`, etc.
- ✅ ALWAYS use semantic measures: `artifacts.count`, `projects.count`
- ❌ NEVER mix WHERE in selects: `"artifacts.artifact_name WHERE ..."`
- ✅ ALWAYS separate: Use `selects` and `filters` arrays
- Only use attributes/relationships defined in the semantic model below
- **IMPORTANT**: Check column types in semantic model. Use proper literals for date/timestamp columns:
  - DATE columns: use `DATE '2023-01-01'` not `'2023-01-01'`
  - TIMESTAMP columns: use `TIMESTAMP '2023-01-01 00:00:00'` not `'2023-01-01'`
  - INTEGER columns with dates: use `20230101` not `'2023-01-01'`

# SEMANTIC MODEL
{semantic_model_description}

# QUERY TO TRANSLATE
{natural_language_query}

# ENTITY CONTEXT
{entity_context}

Return only valid JSON matching the SemanticQuery format above.
"""


async def _translate_nl_to_semantic(
    natural_language_query: str,
    *,
    llm: LLM,
    semantic_model_description: str,
    error_feedback: Optional[str] = None,
    entity_context: Optional[str] = None,
    custom_registry_description: Optional[str] = None,
) -> Response:
    """
    The core logic for the tool. It uses a structured LLM to perform the translation.

    Args:
        natural_language_query: The user's natural language query to translate
        llm: The language model instance to use for translation
        semantic_model_description: Description of the available semantic models
        error_feedback: Optional feedback from previous failed attempts
        entity_context: Optional context about relevant entities from vector database

    Returns:
        Response object containing the structured semantic query
    """
    prompt_template = PromptTemplate(SYSTEM_PROMPT)

    structured_llm = llm.as_structured_llm(StructuredSemanticQuery)

    registry_desc = custom_registry_description or semantic_model_description

    structured_response = await structured_llm.apredict(
        prompt_template,
        natural_language_query=natural_language_query,
        semantic_model_description=registry_desc,
        error_feedback=error_feedback or "",
        entity_context=entity_context or "",
    )

    logger.debug(
        "Translated natural language query '%s' to structured semantic query: %s",
        natural_language_query,
        structured_response,
    )

    return Response(
        response=str(structured_response),
        metadata={"semantic_query": structured_response},
    )


def create_semantic_query_tool(llm: LLM, registry_description: str) -> FunctionTool:
    """
    Factory function to create an instance of the SemanticQueryTool.

    This follows the standard pattern of wrapping a function with baked-in
    dependencies into a FunctionTool.

    Args:
        llm: The language model instance to use for query translation
        registry_description: Description of the semantic model registry

    Returns:
        FunctionTool instance configured for semantic query translation
    """
    tool_fn = partial(
        _translate_nl_to_semantic,
        llm=llm,
        semantic_model_description=registry_description,
    )

    return FunctionTool.from_defaults(
        async_fn=tool_fn,
        name="semantic_query_tool",
        description="Translates a natural language query into a structured semantic query.",
    )
